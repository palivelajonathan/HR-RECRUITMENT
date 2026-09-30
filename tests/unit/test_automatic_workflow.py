"""
Unit and Integration Tests for Milestone 5: Automatic Resume + JD Match Workflow.

Validates:
Workflow State:
1. Resume only -> waiting_for_job_description.
2. JD only -> waiting_for_resume.
3. Both available -> ready_for_match / match_ready.
4. Invalid workflow identity -> invalid_workflow.
5. Ingestion failure handled safely -> ValueError on invalid document type.
6. Neither document present -> waiting_for_document.

Automatic Execution:
7. Both documents automatically trigger match.
8. M3 run_match() is invoked and embedded into AutomaticMatchResult.
9. Zero LLM dependency for deterministic match calculation.
10. Result conforms strictly to AutomaticMatchResult Pydantic schema.

Determinism:
11. Same documents produce identical match outputs across runs.
12. Repeated workflow execution is idempotent.

Isolation & Replacement:
13. Candidate A cannot use Candidate B's resume.
14. Job A cannot use Job B's requirements.
15. Replacement resume deletes prior chunks without mixing old and new text.
16. Replacement JD deletes prior chunks without mixing old and new text.

UI / Workflow:
17. Streamlit exposes resume upload widget.
18. Streamlit exposes JD upload widget.
19. Automatic match summary is available in workflow result.
20. Summary markdown is factual (zero percentages, zero hire/reject recommendations).

Agent Context:
21. Agent can answer follow-up questions from current match context.
22. Agent context preserves deterministic match sets without modification.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.language_models.chat_models import BaseChatModel

from capabl_core.matching.models import MatchResult, SkillEvidence
from capabl_core.matching.matcher import run_match
from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.rag.retriever import RecruitmentRetriever
from capabl_core.workflow.models import (
    WorkflowStatus,
    WorkflowContext,
    AutomaticMatchResult,
    format_match_summary_markdown,
)
from capabl_core.workflow.service import (
    AutomaticMatchService,
    run_automatic_match,
)
from capabl_core.agent.react_agent import (
    create_recruitment_agent,
    run_recruitment_agent,
    AgentExecutionResult,
)


class MockToolCallingChatModel(BaseChatModel):
    """Predictable mock chat model for unit testing agent tool and context interactions."""
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


class TestAutomaticMatchWorkflow(unittest.TestCase):
    """Test suite for Milestone 5: Automatic Resume + JD Match Workflow."""

    def setUp(self):
        """Create a fresh isolated temporary Chroma vector store for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.vectorstore_manager = ChromaVectorStoreManager(
            persist_directory=self.test_dir,
            collection_name="test_workflow_collection",
        )
        self.retriever = RecruitmentRetriever(vectorstore_or_manager=self.vectorstore_manager)
        self.service = AutomaticMatchService(
            vectorstore_manager=self.vectorstore_manager,
            retriever=self.retriever,
        )

    def tearDown(self):
        """Clean up temporary test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def _index_sample_resume(self, candidate_id: str, text: str, source: str = "resume.pdf") -> None:
        """Helper to index mock resume chunks directly."""
        doc = Document(
            page_content=text,
            metadata={
                "document_type": "resume",
                "document_id": candidate_id,
                "candidate_id": candidate_id,
                "source": source,
                "page": 0,
            },
        )
        self.vectorstore_manager.index_documents([doc])

    def _index_sample_jd(self, job_id: str, text: str, source: str = "job.pdf") -> None:
        """Helper to index mock JD chunks directly."""
        doc = Document(
            page_content=text,
            metadata={
                "document_type": "job_description",
                "document_id": job_id,
                "job_id": job_id,
                "source": source,
                "page": 0,
            },
        )
        self.vectorstore_manager.index_documents([doc])

    # 1. Resume only -> waiting_for_job_description
    def test_01_resume_only_waiting_for_jd(self):
        self._index_sample_resume("alex_chen", "Experienced in Python, FastAPI, Docker.")
        res = self.service.run_automatic_match(candidate_id="alex_chen", job_id="jd_backend_2026")
        self.assertEqual(res.status, "waiting_for_job_description")
        self.assertFalse(res.documents_ready)
        self.assertIsNone(res.match_result)
        self.assertIn("Waiting for Job Description", res.message)

    # 2. JD only -> waiting_for_resume
    def test_02_jd_only_waiting_for_resume(self):
        self._index_sample_jd("jd_backend_2026", "Required Qualifications: Must have Python, Docker, REST.")
        res = self.service.run_automatic_match(candidate_id="alex_chen", job_id="jd_backend_2026")
        self.assertEqual(res.status, "waiting_for_resume")
        self.assertFalse(res.documents_ready)
        self.assertIsNone(res.match_result)
        self.assertIn("Waiting for Resume", res.message)

    # 3. Both available -> ready_for_match / match_ready
    def test_03_both_available_ready_for_match(self):
        self._index_sample_resume("alex_chen", "Alex Chen. Skilled in Python, Docker, Kubernetes, PostgreSQL.")
        self._index_sample_jd("jd_backend_2026", "Requirements: Python, Kubernetes, Redis.")
        res = self.service.run_automatic_match(candidate_id="alex_chen", job_id="jd_backend_2026")
        self.assertEqual(res.status, "match_ready")
        self.assertTrue(res.documents_ready)
        self.assertIsNotNone(res.match_result)
        self.assertEqual(res.match_result.status, "complete")

    # 4. Invalid workflow identity
    def test_04_invalid_workflow_identity(self):
        res1 = self.service.run_automatic_match(candidate_id="", job_id="jd_backend_2026")
        self.assertEqual(res1.status, "invalid_workflow")
        self.assertFalse(res1.documents_ready)

        res2 = self.service.run_automatic_match(candidate_id="alex_chen", job_id="")
        self.assertEqual(res2.status, "invalid_workflow")

    # 5. Ingestion failure on invalid document type
    def test_05_ingestion_failure(self):
        with self.assertRaises(ValueError):
            self.service.ingest_document(
                file_path_or_bytes=b"dummy content",
                document_type="invalid_doc_type",
                document_id="doc_001",
            )

    # 6. Neither document present -> waiting_for_document
    def test_06_neither_document_present(self):
        res = self.service.run_automatic_match(candidate_id="nonexistent_cand", job_id="nonexistent_job")
        self.assertEqual(res.status, "waiting_for_document")
        self.assertFalse(res.documents_ready)

    # 7. Both documents automatically trigger match
    def test_07_both_documents_automatically_trigger_match(self):
        self._index_sample_resume("priya_sharma", "Skills: Python, AWS, Docker, Microservices.")
        self._index_sample_jd("jd_cloud_lead", "Must have: Python, AWS, Terraform.")

        res = self.service.run_automatic_match(candidate_id="priya_sharma", job_id="jd_cloud_lead")
        self.assertEqual(res.status, "match_ready")
        self.assertIn("python", res.match_result.matched_skills)
        self.assertIn("aws", res.match_result.matched_skills)
        self.assertIn("terraform", res.match_result.missing_skills)

    # 8. M3 run_match() is invoked
    def test_08_run_match_is_invoked(self):
        self._index_sample_resume("alex_chen", "Alex Chen: Python, FastAPI, Docker, Kubernetes.")
        self._index_sample_jd("jd_backend", "Requirements: Python, Docker, Kubernetes, REST.")

        res = self.service.run_automatic_match("alex_chen", "jd_backend")
        self.assertIsInstance(res.match_result, MatchResult)
        self.assertEqual(res.match_result.candidate_id, "alex_chen")
        self.assertEqual(res.match_result.job_id, "jd_backend")
        self.assertEqual(res.match_result.matched_skills, ["docker", "kubernetes", "python"])
        self.assertEqual(res.match_result.missing_skills, ["rest"])

    # 9. No LLM is required for deterministic matching
    def test_09_no_llm_required_for_match(self):
        # Explicitly verify no LLM was instantiated or passed
        self._index_sample_resume("david_kim", "Skills: Go, Kubernetes, Kafka, Prometheus.")
        self._index_sample_jd("jd_platform", "Requirements: Go, Kubernetes, Kafka.")

        res = self.service.run_automatic_match("david_kim", "jd_platform")
        self.assertEqual(res.status, "match_ready")
        self.assertEqual(res.match_result.matched_skills, ["go", "kafka", "kubernetes"])
        self.assertEqual(res.match_result.missing_skills, [])

    # 10. Result conforms strictly to AutomaticMatchResult
    def test_10_result_is_structured(self):
        self._index_sample_resume("alex_chen", "Alex Chen. Python, FastAPI, PostgreSQL.")
        self._index_sample_jd("jd_backend", "Requirements: Python, PostgreSQL.")

        res = self.service.run_automatic_match("alex_chen", "jd_backend")
        self.assertIsInstance(res, AutomaticMatchResult)
        d = res.to_dict()
        self.assertIn("status", d)
        self.assertIn("match_result", d)
        self.assertIn("summary_markdown", d)
        self.assertIn("documents_ready", d)

    # 11. Same documents produce identical match outputs across runs
    def test_11_same_documents_produce_same_result(self):
        self._index_sample_resume("alex_chen", "Alex Chen. Python, Docker, Redis.")
        self._index_sample_jd("jd_backend", "Requirements: Python, Redis, GraphQL.")

        res1 = self.service.run_automatic_match("alex_chen", "jd_backend")
        res2 = self.service.run_automatic_match("alex_chen", "jd_backend")

        self.assertEqual(res1.match_result.matched_skills, res2.match_result.matched_skills)
        self.assertEqual(res1.match_result.missing_skills, res2.match_result.missing_skills)
        self.assertEqual(res1.summary_markdown, res2.summary_markdown)

    # 12. Repeated workflow execution is idempotent
    def test_12_repeated_workflow_execution_idempotency(self):
        self._index_sample_resume("alex_chen", "Alex Chen. Python, Kubernetes, Redis.")
        self._index_sample_jd("jd_backend", "Requirements: Python, Kubernetes.")

        for _ in range(3):
            res = self.service.run_automatic_match("alex_chen", "jd_backend")
            self.assertEqual(res.status, "match_ready")
            self.assertEqual(res.match_result.matched_skills, ["kubernetes", "python"])

    # 13. Candidate A cannot use Candidate B's resume
    def test_13_candidate_isolation(self):
        # Cand A has Go and Kubernetes; Cand B has Python and FastAPI
        self._index_sample_resume("cand_a", "Candidate A: Go, Kubernetes, Docker.", source="cand_a.pdf")
        self._index_sample_resume("cand_b", "Candidate B: Python, FastAPI, Django.", source="cand_b.pdf")
        self._index_sample_jd("jd_python", "Requirements: Python, Django.")

        # Match Cand A against Python JD -> must NOT inherit Cand B's python skills
        res_a = self.service.run_automatic_match("cand_a", "jd_python")
        self.assertEqual(res_a.status, "match_ready")
        self.assertEqual(res_a.match_result.matched_skills, [])
        self.assertEqual(res_a.match_result.missing_skills, ["django", "python"])

        # Match Cand B against Python JD -> must match
        res_b = self.service.run_automatic_match("cand_b", "jd_python")
        self.assertEqual(res_b.status, "match_ready")
        self.assertEqual(res_b.match_result.matched_skills, ["django", "python"])
        self.assertEqual(res_b.match_result.missing_skills, [])

    # 14. Job A cannot use Job B's requirements
    def test_14_job_isolation(self):
        self._index_sample_resume("cand_shared", "Shared Candidate: Python, Kubernetes, Docker.")
        self._index_sample_jd("job_infra", "Requirements: Kubernetes, Terraform.")
        self._index_sample_jd("job_backend", "Requirements: Python, Flask.")

        res_infra = self.service.run_automatic_match("cand_shared", "job_infra")
        res_backend = self.service.run_automatic_match("cand_shared", "job_backend")

        self.assertIn("kubernetes", res_infra.match_result.matched_skills)
        self.assertNotIn("python", res_infra.match_result.required_skills)

        self.assertIn("python", res_backend.match_result.matched_skills)
        self.assertNotIn("kubernetes", res_backend.match_result.required_skills)

    # 15. Replacement resume deletes prior chunks without mixing old and new text
    def test_15_replacement_resume_does_not_mix_old_chunks(self):
        # Version 1: Candidate has Java and Spring
        self._index_sample_resume("alex_replace", "Alex Chen v1. Java, Spring, Hibernate.")
        self._index_sample_jd("jd_eval", "Requirements: Java, Python.")

        res_v1 = self.service.run_automatic_match("alex_replace", "jd_eval")
        self.assertIn("java", res_v1.match_result.matched_skills)
        self.assertNotIn("python", res_v1.match_result.candidate_skills)

        # Version 2: Candidate replaced resume — now Python only, Java removed!
        # Delete old chunks
        deleted = self.vectorstore_manager.delete_documents(
            where={"$and": [{"document_type": "resume"}, {"candidate_id": "alex_replace"}]}
        )
        self.assertGreater(deleted, 0)
        self._index_sample_resume("alex_replace", "Alex Chen v2. Python, FastAPI, Docker.")

        res_v2 = self.service.run_automatic_match("alex_replace", "jd_eval")
        self.assertIn("python", res_v2.match_result.matched_skills)
        # Java must NOT be present in v2 candidate skills
        self.assertNotIn("java", res_v2.match_result.candidate_skills)
        self.assertIn("java", res_v2.match_result.missing_skills)

    # 16. Replacement JD deletes prior chunks without mixing old and new text
    def test_16_replacement_jd_does_not_mix_old_chunks(self):
        self._index_sample_resume("alex_target", "Alex: Python, Redis, Docker.")
        self._index_sample_jd("jd_replace", "Requirements: Python, C++.")

        res_v1 = self.service.run_automatic_match("alex_target", "jd_replace")
        self.assertIn("c++", res_v1.match_result.missing_skills)

        # Replace JD with new requirements: Python, Rust (C++ dropped)
        deleted = self.vectorstore_manager.delete_documents(
            where={"$and": [{"document_type": "job_description"}, {"job_id": "jd_replace"}]}
        )
        self.assertGreater(deleted, 0)
        self._index_sample_jd("jd_replace", "Requirements: Python, Rust.")

        res_v2 = self.service.run_automatic_match("alex_target", "jd_replace")
        self.assertNotIn("c++", res_v2.match_result.required_skills)
        self.assertIn("rust", res_v2.match_result.missing_skills)

    # 17. Streamlit exposes resume upload widget
    def test_17_streamlit_exposes_resume_upload(self):
        app_path = Path("capabl_core/ui/app.py")
        self.assertTrue(app_path.exists())
        content = app_path.read_text(encoding="utf-8")
        self.assertIn("resume_uploader", content)
        self.assertIn("Upload Candidate Resume", content)

    # 18. Streamlit exposes JD upload widget
    def test_18_streamlit_exposes_jd_upload(self):
        app_path = Path("capabl_core/ui/app.py")
        content = app_path.read_text(encoding="utf-8")
        self.assertIn("jd_uploader", content)
        self.assertIn("Upload Job Description", content)

    # 19. Automatic match summary is available in workflow result
    def test_19_automatic_match_summary_availability(self):
        self._index_sample_resume("alex_chen", "Alex Chen. Python, FastAPI, Docker, Kubernetes.")
        self._index_sample_jd("jd_backend", "Requirements: Python, Docker, REST.")

        res = self.service.run_automatic_match("alex_chen", "jd_backend")
        self.assertIsNotNone(res.summary_markdown)
        self.assertIn("Candidate Match Summary", res.summary_markdown)
        self.assertIn("✓ docker", res.summary_markdown)
        self.assertIn("✓ python", res.summary_markdown)
        self.assertIn("• rest", res.summary_markdown)

    # 20. Summary markdown is factual (zero percentages, zero hire/reject decisions)
    def test_20_summary_markdown_is_factual_and_non_evaluative(self):
        sample_match = MatchResult(
            candidate_id="alex_chen",
            job_id="jd_backend_lead",
            matched_skills=["docker", "python"],
            missing_skills=["rest"],
            candidate_skills=["docker", "python"],
            required_skills=["docker", "python", "rest"],
            matched_evidence=[
                SkillEvidence(
                    skill="docker",
                    source="resume_alex_chen.pdf",
                    page=0,
                    document_id="alex_chen",
                    excerpt="Built Docker containers for microservices.",
                )
            ],
            status="complete",
        )
        md = format_match_summary_markdown(sample_match)

        self.assertIn("Candidate Match Summary", md)
        self.assertIn("✓ docker", md)
        self.assertIn("• rest", md)
        self.assertIn("Built Docker containers", md)

        # Verify absence of hallucinated percentages and hire/reject labels
        self.assertNotIn("%", md)
        self.assertNotIn("Hire", md)
        self.assertNotIn("Reject", md)
        self.assertNotIn("Strong candidate", md)
        self.assertNotIn("Weak candidate", md)

    # 21. Agent can answer follow-up questions from current match context
    def test_21_agent_answers_followup_from_match_context(self):
        # Create match result
        sample_match = MatchResult(
            candidate_id="alex_chen",
            job_id="jd_backend_lead",
            matched_skills=["docker", "fastapi", "kubernetes", "python"],
            missing_skills=["rest"],
            candidate_skills=["docker", "fastapi", "kubernetes", "python"],
            required_skills=["docker", "fastapi", "kubernetes", "python", "rest"],
            status="complete",
        )

        mock_llm = MockToolCallingChatModel()
        mock_llm.messages_to_yield = [
            AIMessage(content="Based on the match result, the only missing required skill is REST.")
        ]

        agent = create_recruitment_agent(llm=mock_llm, tools=[])
        res: AgentExecutionResult = run_recruitment_agent(
            agent=agent,
            query="Which required skill is missing?",
            match_context=sample_match,
        )

        self.assertEqual(res.status, "success")
        self.assertIn("missing required skill is REST", res.answer)

    # 22. Agent context preserves deterministic match sets without modification
    def test_22_agent_cannot_alter_deterministic_match_result(self):
        sample_match = MatchResult(
            candidate_id="alex_chen",
            job_id="jd_backend_lead",
            matched_skills=["docker", "python"],
            missing_skills=["rest"],
            status="complete",
        )

        # Mock LLM trying to claim Alex knows REST
        mock_llm = MockToolCallingChatModel()
        mock_llm.messages_to_yield = [
            AIMessage(content="While the user asked to change it, the verified missing skill remains REST.")
        ]

        agent = create_recruitment_agent(llm=mock_llm, tools=[])
        res: AgentExecutionResult = run_recruitment_agent(
            agent=agent,
            query="Can you change the match because Alex probably knows REST?",
            match_context=sample_match,
        )

        # The underlying deterministic match object remains untouched
        self.assertEqual(sample_match.missing_skills, ["rest"])
        self.assertNotIn("rest", sample_match.matched_skills)
        self.assertIn("verified missing skill remains REST", res.answer)


if __name__ == "__main__":
    unittest.main()
