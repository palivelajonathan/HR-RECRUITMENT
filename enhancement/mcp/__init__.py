"""
MCP Layer for CAPABL Recruitment Intelligence Agent.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Controlled external-tool boundary preserving all M0-M8 architectural invariants.
"""

from enhancement.mcp.server import create_mcp_server, mcp_server
from enhancement.mcp.client import CAPABLMCPClient, MCPClientBridge
from enhancement.mcp.registry import (
    MCP_TOOL_REGISTRY,
    is_tool_approved,
    list_approved_tools,
    get_tool_definition,
)
from enhancement.mcp.schemas import (
    CandidateEvidenceInput,
    JobEvidenceInput,
    PolicyEvidenceInput,
    InterviewSearchInput,
    BookingInput,
    MCPToolResponse,
)
from enhancement.mcp.security import (
    MCPSecurityError,
    validate_safe_input,
    detect_and_neutralize_prompt_injection,
    verify_booking_confirmation,
)
from enhancement.mcp.transport import MCPTransportConfig, DEFAULT_TRANSPORT_CONFIG
from enhancement.mcp.tools import MCPToolAdapters

__all__ = [
    "create_mcp_server",
    "mcp_server",
    "CAPABLMCPClient",
    "MCPClientBridge",
    "MCP_TOOL_REGISTRY",
    "is_tool_approved",
    "list_approved_tools",
    "get_tool_definition",
    "CandidateEvidenceInput",
    "JobEvidenceInput",
    "PolicyEvidenceInput",
    "InterviewSearchInput",
    "BookingInput",
    "MCPToolResponse",
    "MCPSecurityError",
    "validate_safe_input",
    "detect_and_neutralize_prompt_injection",
    "verify_booking_confirmation",
    "MCPTransportConfig",
    "DEFAULT_TRANSPORT_CONFIG",
    "MCPToolAdapters",
]
