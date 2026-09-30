"""
Unit and Integration Tests for Milestone 2: CAPABL Agent Core + Tool Calling.

Validates:
1. Provider Integration: Agent consumes BaseChatModel from create_llm().
2. Tool Registration & Schema: Tools are valid BaseTool instances with typed schemas.
3. Input Validation: Invalid document types fail safely via Pydantic.
4. Retrieval Tool Isolation: Retrieval tool preserves document isolation.
5. Candidate Info Tool: Deterministic metadata lookup without scheduling/matching logic.
6. Agent Execution (Direct Response): General query produces direct answer without tools.
7. Agent Execution (Tool Calling Loop): Tool selection -> tool execution -> evidence integration.
8. Agent Execution (No Evidence): Agent reports unavailable evidence without fabrication.
9. Response Contract: Conforms to AgentExecutionResult (answer, tool_calls, sources, status).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import List, Dict, Any, Optional

from pydantic import ValidationError
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool

from capabl_core.llm import create_llm
from capabl_core.ingestion.pdf_loader import PDFIngestionPipeline
from capabl_core.rag.embeddings import get_embedding_function
from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.rag.retriever import RecruitmentRetriever
from capabl_core.tools.retrieval_tool import (
    RetrievalQueryInput,
    create_retrieval_tool,
    retrieve_evidence,
)
from capabl_core.tools.candidate_info_tool import (
    CandidateInfoInput,
    create_candidate_info_tool,
    get_candidate_profile_info,
    VERIFIED_CANDIDATE_REGISTRY,
)
from capabl_core.agent.react_agent import (
    create_recruitment_agent,
    run_recruitment_agent,
    AgentExecutionResult,
    RECRUITMENT_AGENT_SYSTEM_PROMPT,
)


class MockToolCallingChatModel(BaseChatModel):
    """
    Predictable mock chat model for unit testing LangChain agent loops.
    Supports bind_tools() and generates pre-programmed tool calls and responses.
    """
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


class TestCAPABLAgentCore(unittest.TestCase):
    """Test suite for Milestone 2 Agent Core and Tool Calling."""

    @classmethod
    def setUpClass(cls):
        # Index sample documents into a temporary Chroma store for realistic tool testing
        cls.test_db_dir = tempfile.mkdtemp()
        pipeline = PDFIngestionPipeline()
        sample_dir = Path("./data/sample")

        resume_docs = pipeline.load_and_chunk_pdf(
            file_path=sample_dir / "resumes" / "resume_alex_chen.pdf",
            document_type="resume",
            document_id="alex_chen",
            candidate_id="alex_chen",
        )
        jd_docs = pipeline.load_and_chunk_pdf(
            file_path=sample_dir / "job_descriptions" / "jd_senior_backend_lead.pdf",
            document_type="job_description",
            document_id="jd_senior_backend_lead",
        )
        policy_docs = pipeline.load_and_chunk_pdf(
            file_path=sample_dir / "policies" / "policy_leave_and_attendance.pdf",
            document_type="policy",
            document_id="policy_leave",
        )

        all_docs = resume_docs + jd_docs + policy_docs
        embedding_fn = get_embedding_function()
        cls.store_manager = ChromaVectorStoreManager(
            persist_directory=cls.test_db_dir,
            embedding_function=embedding_fn,
        )
        cls.store_manager.index_documents(all_docs)
        cls.retriever = RecruitmentRetriever(vectorstore_or_manager=cls.store_manager)
        cls.bound_retrieval_tool = create_retrieval_tool(retriever=cls.retriever)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_db_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. Provider Integration
    # -------------------------------------------------------------------------
    def test_provider_integration_uses_base_chat_model(self):
        """Verify that create_recruitment_agent consumes BaseChatModel from create_llm()."""
        llm = create_llm(provider="ollama", model="qwen3:8b")
        self.assertIsInstance(llm, BaseChatModel)

        # Build agent with default tools
        agent_graph = create_recruitment_agent(llm=llm)
        self.assertIsNotNone(agent_graph)
        self.assertTrue(hasattr(agent_graph, "invoke"))

    # -------------------------------------------------------------------------
    # 2. Tool Registration & Schemas
    # -------------------------------------------------------------------------
    def test_tool_registration_and_schemas(self):
        """Verify retrieval and candidate tools are valid LangChain BaseTools with Pydantic schemas."""
        self.assertIsInstance(self.bound_retrieval_tool, BaseTool)
        self.assertIsInstance(get_candidate_profile_info, BaseTool)

        self.assertEqual(self.bound_retrieval_tool.name, "retrieve_evidence")
        self.assertEqual(get_candidate_profile_info.name, "get_candidate_profile_info")

        # Verify arg schemas
        retrieval_schema = self.bound_retrieval_tool.args_schema
        self.assertEqual(retrieval_schema, RetrievalQueryInput)

        candidate_schema = get_candidate_profile_info.args_schema
        self.assertEqual(candidate_schema, CandidateInfoInput)

    # -------------------------------------------------------------------------
    # 3. Input Validation
    # -------------------------------------------------------------------------
    def test_tool_input_validation_rejects_invalid_document_type(self):
        """Verify invalid document type (e.g. 'invoice') is rejected by Pydantic schema."""
        with self.assertRaises(ValidationError):
            RetrievalQueryInput(query="test", document_type="invoice")

        # Valid document types must succeed
        valid_resume = RetrievalQueryInput(query="python", document_type="resume")
        valid_jd = RetrievalQueryInput(query="fastapi", document_type="job_description")
        valid_policy = RetrievalQueryInput(query="annual leave", document_type="policy")
        self.assertEqual(valid_resume.document_type, "resume")
        self.assertEqual(valid_jd.document_type, "job_description")
        self.assertEqual(valid_policy.document_type, "policy")

    # -------------------------------------------------------------------------
    # 4. Retrieval Tool Execution & Document Isolation
    # -------------------------------------------------------------------------
    def test_retrieval_tool_execution_and_isolation(self):
        """Verify retrieval tool returns structured evidence and enforces isolation across types."""
        # Query resumes
        resume_res = self.bound_retrieval_tool.invoke({
            "query": "Kubernetes and Kafka",
            "document_type": "resume",
            "top_k": 3,
        })
        self.assertEqual(resume_res["status"], "success")
        self.assertEqual(resume_res["document_type"], "resume")
        self.assertGreater(resume_res["count"], 0)
        for item in resume_res["results"]:
            self.assertIn("content", item)
            self.assertEqual(item["candidate_id"], "alex_chen")

        # Query policies
        policy_res = self.bound_retrieval_tool.invoke({
            "query": "annual paid leave days",
            "document_type": "policy",
            "top_k": 3,
        })
        self.assertEqual(policy_res["status"], "success")
        self.assertEqual(policy_res["document_type"], "policy")
        self.assertGreater(policy_res["count"], 0)
        for item in policy_res["results"]:
            self.assertIn("leave", item["content"].lower())
            self.assertIsNone(item["candidate_id"])  # Policy documents have no candidate_id

        # Query job descriptions
        jd_res = self.bound_retrieval_tool.invoke({
            "query": "responsibilities and backend requirements",
            "document_type": "job_description",
            "top_k": 3,
        })
        self.assertEqual(jd_res["status"], "success")
        self.assertEqual(jd_res["document_type"], "job_description")
        self.assertGreater(jd_res["count"], 0)

    # -------------------------------------------------------------------------
    # 5. Candidate Info Tool Execution
    # -------------------------------------------------------------------------
    def test_candidate_info_tool_execution(self):
        """Verify deterministic candidate metadata retrieval and graceful not-found handling."""
        known_res = get_candidate_profile_info.invoke({"candidate_id": "alex_chen"})
        self.assertEqual(known_res["status"], "success")
        self.assertEqual(known_res["candidate_id"], "alex_chen")
        self.assertIsNotNone(known_res["profile"])
        self.assertEqual(known_res["profile"]["name"], "Alex Chen")

        unknown_res = get_candidate_profile_info.invoke({"candidate_id": "nonexistent_applicant"})
        self.assertEqual(unknown_res["status"], "not_found")
        self.assertIsNone(unknown_res["profile"])
        self.assertIn("not found in registered profiles", unknown_res["message"])

    # -------------------------------------------------------------------------
    # 6. Agent Direct Response Without Tools
    # -------------------------------------------------------------------------
    def test_agent_direct_response_without_tools(self):
        """Verify agent answers conversational questions directly without triggering tool calls."""
        mock_model = MockToolCallingChatModel(
            messages_to_yield=[
                AIMessage(content="I am the Recruitment Intelligence Agent, ready to assist with candidate searches.")
            ]
        )
        agent = create_recruitment_agent(
            llm=mock_model,
            tools=[self.bound_retrieval_tool, get_candidate_profile_info],
        )

        result = run_recruitment_agent(agent, "Who are you and what do you do?")
        self.assertIsInstance(result, AgentExecutionResult)
        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.tool_calls), 0)
        self.assertEqual(len(result.sources), 0)
        self.assertIn("Recruitment Intelligence Agent", result.answer)

    # -------------------------------------------------------------------------
    # 7. Agent Tool Calling Loop With Retrieval
    # -------------------------------------------------------------------------
    def test_agent_tool_calling_loop_with_retrieval(self):
        """Verify full loop: User query -> Tool call -> Tool execution -> Final answer incorporating evidence."""
        # Step 1: Model emits tool call for resume evidence
        step1_msg = AIMessage(
            content="",
            tool_calls=[{
                "name": "retrieve_evidence",
                "args": {"query": "backend experience and tech stack", "document_type": "resume", "top_k": 2},
                "id": "call_alex_resume_1",
                "type": "tool_call",
            }],
        )
        # Step 2: Model synthesizes final answer after receiving observation
        step2_msg = AIMessage(
            content=(
                "### Evidence:\n"
                "- Alex Chen has 7+ years of experience in distributed systems.\n"
                "- Primary stack includes Python, FastAPI, Kubernetes, and Kafka.\n\n"
                "### Interpretation:\n"
                "Alex meets senior backend criteria based on verified resume data."
            )
        )

        mock_model = MockToolCallingChatModel(messages_to_yield=[step1_msg, step2_msg])
        agent = create_recruitment_agent(
            llm=mock_model,
            tools=[self.bound_retrieval_tool, get_candidate_profile_info],
        )

        result = run_recruitment_agent(agent, "What is Alex Chen's technical background?")
        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0]["tool_name"], "retrieve_evidence")
        self.assertEqual(result.tool_calls[0]["arguments"]["document_type"], "resume")

        # Verify sources were extracted from tool output
        self.assertGreater(len(result.sources), 0)
        self.assertEqual(result.sources[0]["document_type"], "resume")
        self.assertEqual(result.sources[0]["candidate_id"], "alex_chen")

        # Verify final answer content
        self.assertIn("Evidence:", result.answer)
        self.assertIn("Alex Chen has 7+ years of experience", result.answer)

    # -------------------------------------------------------------------------
    # 8. Agent Handles Missing Evidence Gracefully
    # -------------------------------------------------------------------------
    def test_agent_handles_no_evidence_without_fabrication(self):
        """Verify agent handles queries for non-existent documents without fabricating facts."""
        step1_msg = AIMessage(
            content="",
            tool_calls=[{
                "name": "retrieve_evidence",
                "args": {"query": "quantum computing research", "document_type": "policy", "top_k": 2},
                "id": "call_policy_quantum_1",
                "type": "tool_call",
            }],
        )
        step2_msg = AIMessage(
            content=(
                "### Missing Information:\n"
                "No policy evidence regarding quantum computing was found in company documentation. "
                "I cannot provide guidelines on this topic as evidence is unavailable."
            )
        )

        mock_model = MockToolCallingChatModel(messages_to_yield=[step1_msg, step2_msg])
        agent = create_recruitment_agent(
            llm=mock_model,
            tools=[self.bound_retrieval_tool, get_candidate_profile_info],
        )

        result = run_recruitment_agent(agent, "What is the policy on quantum computing?")
        self.assertIn("Missing Information", result.answer)
        self.assertIn("evidence is unavailable", result.answer)

    # -------------------------------------------------------------------------
    # 9. Agent Response Contract Verification
    # -------------------------------------------------------------------------
    def test_agent_execution_result_schema(self):
        """Verify AgentExecutionResult Pydantic schema validation."""
        valid_res = AgentExecutionResult(
            answer="Candidate satisfies criteria.",
            tool_calls=[{"tool_name": "retrieve_evidence", "arguments": {}}],
            sources=[{"source": "test.pdf", "page": 0}],
            status="success",
        )
        self.assertEqual(valid_res.status, "success")
        self.assertEqual(len(valid_res.sources), 1)

        # Invalid status must fail
        with self.assertRaises(ValidationError):
            AgentExecutionResult(
                answer="Test",
                status="invalid_status",  # type: ignore
            )


if __name__ == "__main__":
    unittest.main()
