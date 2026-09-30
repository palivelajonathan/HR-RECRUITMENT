"""
Unit and Integration Tests for Milestone 3: Deterministic Resume ↔ JD Match Engine.

Validates:
1. Skill Normalization: Case-insensitivity, synonym aliases (Postgres, JS, TS, K8s, ReactJS).
2. Deterministic Set-Based Matching: Exact computation of matched and missing sets.
3. No False Matching: Unrelated technologies and generic words do not match.
4. Evidence Linking: Matched skills link to verifiable resume citations (source, page, excerpt).
5. Missing Evidence Integrity: Missing skills receive no fabricated resume evidence.
6. Document Isolation: Resume skills come only from resumes, JD from JDs, policies excluded.
7. Determinism: Repeated evaluations produce identical outputs.
8. Tool Schema: match_resume_to_job is a valid BaseTool adhering to MatchResumeToJobInput.
9. Agent Integration: LangChain agent invokes match_resume_to_job and formats factual output.
10. Graceful Degradation: Empty or missing documents return insufficient_evidence without crash.
"""

import tempfile
import shutil
import unittest
from pathlib import Path
from typing import List, Dict, Any, Optional

from pydantic import ValidationError
from langchain_core.documents import Document
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.language_models.chat_models import BaseChatModel

from capabl_core.matching import (
    SkillEvidence,
    MatchResult,
    normalize_skill,
    SKILL_ALIASES,
    extract_skills_from_text,
    extract_skills_with_evidence,
    extract_required_skills,
    compute_deterministic_match,
    run_match,
)
from capabl_core.tools.match_tool import (
    MatchResumeToJobInput,
    match_resume_to_job,
    create_match_tool,
)
from capabl_core.agent.react_agent import (
    create_recruitment_agent,
    run_recruitment_agent,
    AgentExecutionResult,
)
from capabl_core.ingestion.pdf_loader import PDFIngestionPipeline
from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.rag.retriever import RecruitmentRetriever


class MockToolCallingChatModel(BaseChatModel):
    """Predictable mock chat model for unit testing agent tool invocation."""
    messages_to_yield: List[AIMessage] = []
    current_index: int = 0

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.current_index < len(self.messages_to_yield):
            response_msg = self.messages_to_yield[self.current_index]
            self.current_index += 1
        else:
            response_msg = AIMessage(content="Default mock final answer.")
        return ChatResult(generations=[ChatGeneration(message=response_msg)])

    @property
    def _llm_type(self) -> str:
        return "mock-tool-calling-chat-model"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self


class TestDeterministicMatchEngine(unittest.TestCase):
    """Milestone 3 Deterministic Match Engine Test Suite."""

    @classmethod
    def setUpClass(cls):
        # Index sample documents into a temporary Chroma store for realistic integration testing
        cls.test_db_dir = tempfile.mkdtemp()
        pipeline = PDFIngestionPipeline()
        sample_dir = Path("./data/sample")

        cls.resume_docs = pipeline.load_and_chunk_pdf(
            file_path=sample_dir / "resumes" / "resume_alex_chen.pdf",
            document_type="resume",
            document_id="alex_chen",
            candidate_id="alex_chen",
        )
        cls.jd_docs = pipeline.load_and_chunk_pdf(
            file_path=sample_dir / "job_descriptions" / "jd_senior_backend_lead.pdf",
            document_type="job_description",
            document_id="jd_backend_lead_2026",
        )
        cls.policy_docs = pipeline.load_and_chunk_pdf(
            file_path=sample_dir / "policies" / "policy_leave_and_attendance.pdf",
            document_type="policy",
            document_id="policy_leave_2026",
        )

        cls.vector_manager = ChromaVectorStoreManager(persist_directory=cls.test_db_dir)
        cls.vector_manager.add_documents(cls.resume_docs + cls.jd_docs + cls.policy_docs)
        cls.retriever = RecruitmentRetriever(vectorstore_or_manager=cls.vector_manager)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_db_dir, ignore_errors=True)

    # 1. Normalization Tests
    def test_skill_normalization_case_and_aliases(self):
        """Validates case-insensitivity and synonym alias mapping."""
        # Case insensitivity
        self.assertEqual(normalize_skill("Python"), "python")
        self.assertEqual(normalize_skill("python"), "python")
        self.assertEqual(normalize_skill("PYTHON"), "python")

        # Database aliases
        self.assertEqual(normalize_skill("Postgres"), "postgresql")
        self.assertEqual(normalize_skill("PostgreSQL"), "postgresql")
        self.assertEqual(normalize_skill("psql"), "postgresql")

        # Language aliases
        self.assertEqual(normalize_skill("JS"), "javascript")
        self.assertEqual(normalize_skill("JavaScript"), "javascript")
        self.assertEqual(normalize_skill("TS"), "typescript")
        self.assertEqual(normalize_skill("TypeScript"), "typescript")
        self.assertEqual(normalize_skill("Golang"), "go")

        # Framework and Infra aliases
        self.assertEqual(normalize_skill("K8s"), "kubernetes")
        self.assertEqual(normalize_skill("Kubernetes"), "kubernetes")
        self.assertEqual(normalize_skill("ReactJS"), "react")
        self.assertEqual(normalize_skill("react.js"), "react")
        self.assertEqual(normalize_skill("NextJS"), "next.js")
        self.assertEqual(normalize_skill("NodeJS"), "node.js")

        # Edge cases and punctuation
        self.assertEqual(normalize_skill("  C++  "), "c++")
        self.assertEqual(normalize_skill(".NET"), ".net")
        self.assertEqual(normalize_skill(""), "")

    # 2. Deterministic Matching Algorithm Tests
    def test_deterministic_set_based_matching(self):
        """Validates exact set intersection and difference logic."""
        jd_required = ["Python", "FastAPI", "PostgreSQL", "Kubernetes"]
        resume_skills = ["Python", "FastAPI", "PostgreSQL"]

        result = compute_deterministic_match(
            candidate_id="cand_alex",
            job_id="job_backend",
            candidate_skills=resume_skills,
            required_skills=jd_required,
        )

        self.assertEqual(result.matched_skills, ["fastapi", "postgresql", "python"])
        self.assertEqual(result.missing_skills, ["kubernetes"])
        self.assertEqual(result.status, "complete")

    # 3. No False Matching
    def test_no_false_matching(self):
        """Ensures unrelated skills or substring names do not falsely match."""
        jd_required = ["Ruby", "COBOL", "Scala"]
        resume_skills = ["Python", "FastAPI", "Docker", "PostgreSQL"]

        result = compute_deterministic_match(
            candidate_id="cand_alex",
            job_id="job_legacy",
            candidate_skills=resume_skills,
            required_skills=jd_required,
        )

        self.assertEqual(result.matched_skills, [])
        self.assertEqual(result.missing_skills, ["cobol", "ruby", "scala"])

    # 4. Evidence Linking for Matched Skills
    def test_evidence_linking_on_matched_skills(self):
        """Verifies matched skills link to valid resume excerpts and metadata."""
        candidate_evidence = extract_skills_with_evidence(
            documents_or_text=self.resume_docs,
            default_source="resume_alex_chen.pdf",
            default_document_id="alex_chen",
        )

        self.assertIn("python", candidate_evidence)
        self.assertIn("fastapi", candidate_evidence)
        self.assertIn("kubernetes", candidate_evidence)

        # Check excerpt quality
        python_ev = candidate_evidence["python"][0]
        self.assertIsInstance(python_ev, SkillEvidence)
        self.assertEqual(python_ev.skill, "python")
        self.assertTrue("python" in python_ev.excerpt.lower())
        self.assertTrue("resume" in python_ev.source.lower())

    # 5. Missing Evidence Integrity
    def test_missing_skills_receive_no_fabricated_evidence(self):
        """Confirms missing skills have zero resume citations attached."""
        jd_required = ["Kubernetes", "Solidity"]
        resume_skills = ["Kubernetes"]

        evidence_map = {
            "kubernetes": [
                SkillEvidence(
                    skill="kubernetes",
                    source="resume_alex_chen.pdf",
                    page=0,
                    excerpt="Orchestrated container workloads using Kubernetes and Helm.",
                )
            ]
        }

        result = compute_deterministic_match(
            candidate_id="alex_chen",
            job_id="job_web3",
            candidate_skills=resume_skills,
            required_skills=jd_required,
            candidate_evidence_map=evidence_map,
        )

        self.assertEqual(result.matched_skills, ["kubernetes"])
        self.assertEqual(result.missing_skills, ["solidity"])

        # Matched skill has evidence
        self.assertEqual(len(result.matched_evidence), 1)
        self.assertEqual(result.matched_evidence[0].skill, "kubernetes")

        # Zero evidence created for solidity
        for ev in result.matched_evidence:
            self.assertNotEqual(ev.skill, "solidity")

    # 6. Document Isolation in Skill Extraction
    def test_document_isolation_in_skill_matching(self):
        """Verifies policy documents do not contaminate candidate or JD skills."""
        policy_skills = extract_skills_from_text(
            "\n".join(d.page_content for d in self.policy_docs)
        )
        # Policies should not contain technical skills
        self.assertEqual(policy_skills, [])

        # Candidate skills are strictly extracted from resumes
        candidate_ev = extract_skills_with_evidence(self.resume_docs)
        candidate_skills = list(candidate_ev.keys())
        self.assertIn("python", candidate_skills)
        self.assertIn("docker", candidate_skills)

    # 7. Determinism Guarantee
    def test_determinism_multiple_runs(self):
        """Asserts that identical inputs produce 100% reproducible results."""
        runs = []
        for _ in range(5):
            res = compute_deterministic_match(
                candidate_id="cand_01",
                job_id="jd_01",
                candidate_skills=["Python", "FastAPI", "Redis"],
                required_skills=["Python", "FastAPI", "Kubernetes", "Redis"],
            )
            runs.append(res.model_dump())

        # All 5 runs must be bitwise identical
        for i in range(1, len(runs)):
            self.assertEqual(runs[0], runs[i])

    # 8. LangChain Tool Schema Validation
    def test_match_tool_schema_and_registration(self):
        """Verifies match_resume_to_job is a valid BaseTool adhering to MatchResumeToJobInput."""
        custom_tool = create_match_tool(retriever=self.retriever)
        self.assertIsInstance(custom_tool, BaseTool)
        self.assertEqual(custom_tool.name, "match_resume_to_job")

        # Input schema check
        schema = custom_tool.args_schema
        self.assertEqual(schema, MatchResumeToJobInput)

        # Valid input parsing
        valid_input = MatchResumeToJobInput(candidate_id="alex_chen", job_id="jd_backend_lead_2026")
        self.assertEqual(valid_input.candidate_id, "alex_chen")
        self.assertEqual(valid_input.job_id, "jd_backend_lead_2026")

        # Invalid input rejects missing fields
        with self.assertRaises(ValidationError):
            MatchResumeToJobInput(candidate_id="")  # Missing job_id

    # 9. Automatic Match API End-to-End Execution
    def test_run_match_end_to_end(self):
        """Validates programmatic run_match() against the indexed vector store."""
        result = run_match(
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            retriever=self.retriever,
        )

        self.assertEqual(result.status, "complete")
        self.assertEqual(result.candidate_id, "alex_chen")
        self.assertEqual(result.job_id, "jd_backend_lead_2026")

        # Alex Chen has Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis
        self.assertIn("python", result.matched_skills)
        self.assertIn("fastapi", result.matched_skills)
        self.assertIn("docker", result.matched_skills)
        self.assertIn("kubernetes", result.matched_skills)
        self.assertIn("postgresql", result.matched_skills)
        self.assertIn("redis", result.matched_skills)

        # Matched evidence is populated
        self.assertTrue(len(result.matched_evidence) > 0)
        skills_in_ev = {ev.skill for ev in result.matched_evidence}
        self.assertIn("python", skills_in_ev)

    # 10. Agent Integration Test via Mock Tool Calling
    def test_agent_invokes_match_tool(self):
        """Tests that the LangChain recruitment agent can invoke match_resume_to_job."""
        mock_llm = MockToolCallingChatModel()
        tool_instance = create_match_tool(retriever=self.retriever)

        # Step 1: Agent decides to call match_resume_to_job
        mock_llm.messages_to_yield = [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "match_resume_to_job",
                        "args": {"candidate_id": "alex_chen", "job_id": "jd_backend_lead_2026"},
                        "id": "call_match_001",
                    }
                ],
            ),
            # Step 2: Agent summarizes the factual output
            AIMessage(
                content=(
                    "### Candidate Match Evaluation:\n"
                    "EVIDENCE:\n"
                    "- Matched Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis.\n"
                    "INTERPRETATION:\n"
                    "- Candidate Alex Chen fulfills the core technical requirements for the Senior Backend Lead role.\n"
                    "MISSING INFORMATION:\n"
                    "- None."
                )
            ),
        ]

        agent = create_recruitment_agent(
            llm=mock_llm,
            tools=[tool_instance],
        )

        exec_result: AgentExecutionResult = run_recruitment_agent(
            agent=agent,
            query="Match candidate alex_chen with job description jd_backend_lead_2026.",
        )

        self.assertEqual(exec_result.status, "success")
        self.assertEqual(len(exec_result.tool_calls), 1)
        self.assertEqual(exec_result.tool_calls[0]["tool_name"], "match_resume_to_job")
        self.assertIn("Matched Skills", exec_result.answer)
        self.assertTrue(len(exec_result.sources) > 0)

    # 11. Graceful Degradation on Missing Documents
    def test_graceful_handling_of_missing_documents(self):
        """Confirms that nonexistent candidate/job IDs return insufficient_evidence without crashing."""
        result = run_match(
            candidate_id="nonexistent_candidate_999",
            job_id="nonexistent_job_888",
            retriever=self.retriever,
        )

        self.assertEqual(result.status, "insufficient_evidence")
        self.assertEqual(result.matched_skills, [])
        self.assertEqual(result.missing_skills, [])
        self.assertIn("could not locate", result.message.lower())


if __name__ == "__main__":
    unittest.main()
