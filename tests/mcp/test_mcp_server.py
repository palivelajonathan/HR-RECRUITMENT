"""
Tests for FastMCP Server for CAPABL Recruitment Intelligence Agent.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Verifies:
- Server instantiation and configuration
- Approved tools are registered and exposed
- Unapproved tools are not available
- Tool definitions and parameter schemas
"""

import pytest
from mcp.server.fastmcp import FastMCP
from enhancement.mcp.server import create_mcp_server, mcp_server
from enhancement.mcp.registry import MCP_TOOL_REGISTRY, is_tool_approved, list_approved_tools


class TestMCPServerConfiguration:

    def test_01_server_instantiation(self):
        """Verify FastMCP server is instantiated with correct name."""
        server = create_mcp_server()
        assert isinstance(server, FastMCP)
        assert server.name == "capabl_recruitment_mcp"

    def test_02_approved_tools_exposed(self):
        """Verify all 5 approved tools are exposed on the server."""
        server = create_mcp_server()
        exposed_tool_names = [t.name for t in server._tool_manager.list_tools()]
        expected_tools = [
            "get_candidate_evidence",
            "get_job_evidence",
            "get_policy_evidence",
            "search_interview_slots",
            "book_interview",
        ]
        for expected in expected_tools:
            assert expected in exposed_tool_names, f"Expected tool '{expected}' missing from MCP server"

    def test_03_unapproved_tools_unavailable(self):
        """Verify unapproved tools are not exposed on the server."""
        server = create_mcp_server()
        exposed_tool_names = [t.name for t in server._tool_manager.list_tools()]
        unapproved = [
            "arbitrary_code_exec",
            "drop_database",
            "delete_candidate",
            "read_passwords",
            "execute_shell",
        ]
        for unapp in unapproved:
            assert unapp not in exposed_tool_names, f"Unapproved tool '{unapp}' unexpectedly found on server"

    def test_04_tool_count_matches_registry(self):
        """Verify the number of exposed tools exactly matches the approved registry."""
        server = create_mcp_server()
        exposed_tool_names = [t.name for t in server._tool_manager.list_tools()]
        assert len(exposed_tool_names) == len(MCP_TOOL_REGISTRY)
        assert set(exposed_tool_names) == set(MCP_TOOL_REGISTRY.keys())

    def test_05_singleton_server_available(self):
        """Verify global singleton mcp_server is available and configured."""
        assert mcp_server is not None
        assert isinstance(mcp_server, FastMCP)
        exposed_tool_names = [t.name for t in mcp_server._tool_manager.list_tools()]
        assert "get_candidate_evidence" in exposed_tool_names
