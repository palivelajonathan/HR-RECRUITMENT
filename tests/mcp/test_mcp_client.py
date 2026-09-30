"""
Tests for MCP Client Boundary.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Verifies:
- CAPABLMCPClient discovery, invocation, and error handling
- Unapproved tool rejection
- LangChain BaseTool wrapper generation
- Backward compatibility with MCPClientBridge
"""

import json
import pytest
from langchain_core.tools import BaseTool

from enhancement.mcp.client import CAPABLMCPClient, MCPClientBridge, normalize_mcp_response
from enhancement.mcp.registry import list_approved_tools
from enhancement.mcp.schemas import MCPToolResponse
from evaluation.runners.retrieval_runner import ensure_test_documents_indexed
from capabl_core.workflow.service import AutomaticMatchService
from capabl_core.rag.vectorstore import ChromaVectorStoreManager


class TestMCPClientBoundary:

    def test_01_client_initialization(self):
        """Verify client initializes cleanly."""
        client = CAPABLMCPClient()
        assert client is not None
        assert client.config.transport_type == "stdio"

    def test_02_client_list_tools(self):
        """Verify client lists all approved tools with metadata."""
        client = CAPABLMCPClient()
        tools = client.list_tools()
        assert len(tools) == 5
        names = [t["name"] for t in tools]
        for approved in list_approved_tools():
            assert approved in names

    def test_03_client_rejects_unapproved_tool(self):
        """Verify client blocks requests to unapproved tools."""
        client = CAPABLMCPClient()
        res = client.call_tool("unapproved_hacker_tool", {"arg": "val"})
        assert res["status"] == "blocked"
        assert res["error_code"] == "UNAPPROVED_TOOL"
        assert "unapproved" in res["message"].lower()

    def test_04_langchain_tools_conversion(self):
        """Verify client generates valid LangChain BaseTools."""
        client = CAPABLMCPClient()
        lc_tools = client.get_langchain_tools()
        assert len(lc_tools) == 5
        for tool_obj in lc_tools:
            assert isinstance(tool_obj, BaseTool)
            assert tool_obj.name.startswith("mcp_")
            assert tool_obj.description is not None

    def test_05_langchain_tool_invocation(self):
        """Verify LangChain tool wrapper can be invoked."""
        client = CAPABLMCPClient()
        lc_tools = client.get_langchain_tools()
        policy_tool = next(t for t in lc_tools if t.name == "mcp_policy_evidence")

        # Invoke tool with valid input
        result = policy_tool.invoke({"query": "What is the annual leave allowance?"})
        assert isinstance(result, dict)
        assert result.get("status") in ("success", "blocked")
        assert result.get("tool") == "get_policy_evidence"

    def test_06_backward_compatibility_bridge(self):
        """Verify MCPClientBridge works as subclass of CAPABLMCPClient."""
        bridge = MCPClientBridge()
        assert isinstance(bridge, CAPABLMCPClient)
        tools = bridge.list_tools()
        assert len(tools) == 5

    def test_07_mcp_candidate_evidence_ui_response_shape(self):
        """
        Regression Test for M10 UI Evidence Explorer:
        Verify candidate evidence retrieved via MCP client returns a stable,
        typed dictionary with non-None 'data', structured 'items', and 'evidence',
        preventing 'NoneType' object has no attribute 'get'.
        """
        mgr = ChromaVectorStoreManager()
        service = AutomaticMatchService(vectorstore_manager=mgr)
        ensure_test_documents_indexed(service)

        client = CAPABLMCPClient()
        resp = client.call_tool("get_candidate_evidence", {
            "candidate_id": "alex_chen",
            "query": "distributed systems and microservices experience",
            "top_k": 3,
        })

        assert isinstance(resp, dict), "Response must be a structured dictionary"
        assert resp.get("status") == "success"
        assert resp.get("tool") == "get_candidate_evidence"
        assert resp.get("candidate_id") == "alex_chen"

        # 1. Official MCP evidence list contract
        assert isinstance(resp.get("evidence"), list), "resp['evidence'] must be a list"
        assert len(resp["evidence"]) > 0, "Expected non-empty evidence list for Alex Chen"

        # 2. 'data' must NEVER be None
        assert resp.get("data") is not None, "resp['data'] must not be None"
        assert isinstance(resp.get("data"), dict), "resp['data'] must be a dictionary"

        # 3. Streamlit UI parsing expressions must both evaluate safely without raising AttributeError
        # Expression A (legacy UI expression):
        legacy_items = resp.get("data", {}).get("items", [])
        assert isinstance(legacy_items, list)
        assert len(legacy_items) == len(resp["evidence"])

        # Expression B (hardened UI expression):
        ui_items = resp.get("evidence") or (resp.get("data") or {}).get("items", [])
        assert isinstance(ui_items, list)
        assert len(ui_items) == len(resp["evidence"])

        # 4. Verify candidate isolation and document_type filtering preserved on each item
        for item in ui_items:
            assert isinstance(item, dict)
            assert item.get("candidate_id") == "alex_chen"
            assert item.get("document_type") == "resume"
            assert "excerpt" in item and len(item["excerpt"]) > 0
            assert "source" in item

    def test_08_normalize_mcp_response_wrapper_variants(self):
        """
        Verify response normalization succeeds across:
        - Structured dictionary
        - MCP content wrapper dictionary
        - MCP CallToolResult object with .content attribute
        - JSON text content string
        """
        sample_evidence = [{
            "document_type": "resume",
            "document_id": "resume_alex_chen",
            "source": "data/sample_documents/resume_alex_chen.pdf",
            "page": 0,
            "excerpt": "Senior Backend Engineer with 8 years building distributed systems.",
            "candidate_id": "alex_chen",
            "job_id": None,
            "policy_category": None,
        }]

        # 1. Structured dictionary input
        dict_input = {
            "status": "success",
            "tool": "get_candidate_evidence",
            "candidate_id": "alex_chen",
            "evidence": sample_evidence,
            "data": None,
        }
        norm1 = normalize_mcp_response(dict_input, tool_name="get_candidate_evidence")
        assert norm1["status"] == "success"
        assert norm1["data"] is not None
        assert norm1.get("data", {}).get("items") == sample_evidence
        assert norm1.get("evidence") == sample_evidence

        # 2. JSON text content input
        json_input = json.dumps(dict_input)
        norm2 = normalize_mcp_response(json_input, tool_name="get_candidate_evidence")
        assert norm2["status"] == "success"
        assert norm2["data"] is not None
        assert norm2.get("data", {}).get("items") == sample_evidence
        assert norm2.get("evidence") == sample_evidence

        # 3. MCP content wrapper dictionary input
        wrapper_dict_input = {
            "content": [{"type": "text", "text": json.dumps(dict_input)}],
            "isError": False,
        }
        norm3 = normalize_mcp_response(wrapper_dict_input, tool_name="get_candidate_evidence")
        assert norm3["status"] == "success"
        assert norm3["data"] is not None
        assert norm3.get("data", {}).get("items") == sample_evidence
        assert norm3.get("evidence") == sample_evidence

        # 4. MCP object with .content attribute
        class MockTextContent:
            def __init__(self, text):
                self.type = "text"
                self.text = text

        class MockCallToolResult:
            def __init__(self, content):
                self.content = content

        obj_input = MockCallToolResult(content=[MockTextContent(text=json.dumps(dict_input))])
        norm4 = normalize_mcp_response(obj_input, tool_name="get_candidate_evidence")
        assert norm4["status"] == "success"
        assert norm4["data"] is not None
        assert norm4.get("data", {}).get("items") == sample_evidence
        assert norm4.get("evidence") == sample_evidence
