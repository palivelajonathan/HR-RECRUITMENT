"""
Tests for MCP Tool Adapters and Execution Correctness.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Verifies:
- Candidate evidence tool execution
- Job evidence tool execution
- Policy evidence tool execution
- Calendar slot search
- Consequential booking execution
"""

import pytest
from enhancement.mcp.client import CAPABLMCPClient
from evaluation.runners.retrieval_runner import ensure_test_documents_indexed
from capabl_core.workflow.service import AutomaticMatchService
from capabl_core.rag.vectorstore import ChromaVectorStoreManager


@pytest.fixture(scope="module")
def indexed_env():
    mgr = ChromaVectorStoreManager()
    service = AutomaticMatchService(vectorstore_manager=mgr)
    ensure_test_documents_indexed(service)
    return mgr


class TestMCPToolExecution:

    def test_01_candidate_evidence_execution(self, indexed_env):
        """Verify candidate evidence retrieval via MCP returns structured envelope."""
        client = CAPABLMCPClient()
        res = client.call_tool("get_candidate_evidence", {
            "candidate_id": "alex_chen",
            "query": "What experience does Alex Chen have with distributed systems?",
            "top_k": 3,
        })
        assert res["status"] == "success"
        assert res["tool"] == "get_candidate_evidence"
        assert res["candidate_id"] == "alex_chen"
        assert isinstance(res["evidence"], list)

    def test_02_job_evidence_execution(self, indexed_env):
        """Verify job evidence retrieval via MCP returns structured envelope."""
        client = CAPABLMCPClient()
        res = client.call_tool("get_job_evidence", {
            "job_id": "jd_backend_lead_2026",
            "query": "What are the core backend requirements?",
            "top_k": 3,
        })
        assert res["status"] == "success"
        assert res["tool"] == "get_job_evidence"
        assert res["job_id"] == "jd_backend_lead_2026"
        assert isinstance(res["evidence"], list)

    def test_03_policy_evidence_execution(self, indexed_env):
        """Verify policy evidence retrieval via MCP returns structured envelope."""
        client = CAPABLMCPClient()
        res = client.call_tool("get_policy_evidence", {
            "query": "What is the policy on probation and employee leave?",
            "top_k": 3,
        })
        assert res["status"] == "success"
        assert res["tool"] == "get_policy_evidence"
        assert isinstance(res["evidence"], list)

    def test_04_search_slots_execution(self, indexed_env):
        """Verify mock calendar slot search returns available slots."""
        client = CAPABLMCPClient()
        res = client.call_tool("search_interview_slots", {
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "timezone": "Asia/Kolkata",
        })
        assert res["status"] == "success"
        assert res["tool"] == "search_interview_slots"
        assert "data" in res
        assert "slots" in res["data"]
