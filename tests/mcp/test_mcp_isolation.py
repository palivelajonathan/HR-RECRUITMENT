"""
Domain and Entity Isolation Tests for MCP Layer.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Verifies strict isolation:
- Candidate -> Candidate data only (Alex != Priya)
- Policy -> Policy data only (no candidate or JD data)
- Job -> Job data only
"""

import json
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


class TestMCPIsolation:

    def test_01_candidate_alex_does_not_leak_priya(self, indexed_env):
        """Querying Alex Chen's evidence must never return Priya Sharma's details."""
        client = CAPABLMCPClient()
        res = client.call_tool("get_candidate_evidence", {
            "candidate_id": "alex_chen",
            "query": "Tell me about React frontend experience and past employment.",
            "top_k": 4,
        })
        assert res["status"] == "success"
        serialized = json.dumps(res).lower()
        assert "priya sharma" not in serialized
        assert "cand_priya_sharma" not in serialized
        assert "designhub" not in serialized

    def test_02_candidate_priya_does_not_leak_alex(self, indexed_env):
        """Querying Priya Sharma's evidence must never return Alex Chen's details."""
        client = CAPABLMCPClient()
        res = client.call_tool("get_candidate_evidence", {
            "candidate_id": "priya_sharma",
            "query": "Tell me about distributed systems, Python, and backend infrastructure.",
            "top_k": 4,
        })
        assert res["status"] == "success"
        serialized = json.dumps(res).lower()
        assert "alex chen" not in serialized
        assert "cand_alex_chen" not in serialized

    def test_03_policy_evidence_does_not_leak_candidates(self, indexed_env):
        """Policy retrieval must strictly return policy documents without candidate data."""
        client = CAPABLMCPClient()
        res = client.call_tool("get_policy_evidence", {
            "query": "What is the compensation, bonus structure, and leave policy?",
            "top_k": 4,
        })
        assert res["status"] == "success"
        serialized = json.dumps(res).lower()
        assert "alex chen" not in serialized
        assert "priya sharma" not in serialized

    def test_04_job_evidence_does_not_leak_candidate_resumes(self, indexed_env):
        """Job requirements retrieval must not leak candidate resumes."""
        client = CAPABLMCPClient()
        res = client.call_tool("get_job_evidence", {
            "job_id": "jd_backend_lead_2026",
            "query": "What are the required qualifications and experience?",
            "top_k": 4,
        })
        assert res["status"] == "success"
        serialized = json.dumps(res).lower()
        assert "alex chen" not in serialized
        assert "priya sharma" not in serialized
