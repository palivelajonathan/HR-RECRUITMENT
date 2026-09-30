"""
Explicit Tool Registry for MCP External Boundary.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Every exposed MCP tool is explicitly declared with classification,
schema contracts, sensitivity level, authorization prerequisites, and timeouts.
No implicit tool exposure.
"""

from typing import Dict, Any, Type, Optional
from pydantic import BaseModel, ConfigDict

from enhancement.mcp.schemas import (
    CandidateEvidenceInput,
    JobEvidenceInput,
    PolicyEvidenceInput,
    InterviewSearchInput,
    BookingInput,
    MCPToolResponse,
)

MCP_DEFAULT_TIMEOUT_SECONDS = 30


class MCPToolDefinition(BaseModel):
    """Metadata and security classification for an approved MCP tool."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel] = MCPToolResponse
    sensitivity: str  # "low", "medium", "high"
    authorization_requirement: str  # "read", "confirmed_booking"
    timeout_seconds: int = MCP_DEFAULT_TIMEOUT_SECONDS
    audit_event: str
    is_consequential: bool  # False = Read-only; True = State-changing
    allows_state_mutation: bool


MCP_TOOL_REGISTRY: Dict[str, MCPToolDefinition] = {
    "get_candidate_evidence": MCPToolDefinition(
        name="get_candidate_evidence",
        description=(
            "Retrieve verified candidate qualifications, experience, and skills strictly from their resume. "
            "Scoped strictly to the provided candidate_id. Read-only operation."
        ),
        input_schema=CandidateEvidenceInput,
        output_schema=MCPToolResponse,
        sensitivity="high",
        authorization_requirement="read",
        timeout_seconds=MCP_DEFAULT_TIMEOUT_SECONDS,
        audit_event="mcp_candidate_evidence_accessed",
        is_consequential=False,
        allows_state_mutation=False,
    ),
    "get_job_evidence": MCPToolDefinition(
        name="get_job_evidence",
        description=(
            "Retrieve job requirements, mandatory qualifications, and responsibilities for a specific job_id. "
            "Read-only operation."
        ),
        input_schema=JobEvidenceInput,
        output_schema=MCPToolResponse,
        sensitivity="medium",
        authorization_requirement="read",
        timeout_seconds=MCP_DEFAULT_TIMEOUT_SECONDS,
        audit_event="mcp_job_evidence_accessed",
        is_consequential=False,
        allows_state_mutation=False,
    ),
    "get_policy_evidence": MCPToolDefinition(
        name="get_policy_evidence",
        description=(
            "Retrieve authoritative company HR, compensation, benefits, or hiring policy facts. "
            "Read-only operation. Isolated from candidate and JD documents."
        ),
        input_schema=PolicyEvidenceInput,
        output_schema=MCPToolResponse,
        sensitivity="medium",
        authorization_requirement="read",
        timeout_seconds=MCP_DEFAULT_TIMEOUT_SECONDS,
        audit_event="mcp_policy_evidence_accessed",
        is_consequential=False,
        allows_state_mutation=False,
    ),
    "search_interview_slots": MCPToolDefinition(
        name="search_interview_slots",
        description=(
            "Search available interview slots in the interview calendar. "
            "Filters by candidate, job, date range, and duration. Read-only non-consequential operation."
        ),
        input_schema=InterviewSearchInput,
        output_schema=MCPToolResponse,
        sensitivity="low",
        authorization_requirement="read",
        timeout_seconds=MCP_DEFAULT_TIMEOUT_SECONDS,
        audit_event="mcp_interview_slots_queried",
        is_consequential=False,
        allows_state_mutation=False,
    ),
    "book_interview": MCPToolDefinition(
        name="book_interview",
        description=(
            "Book an interview slot in the calendar. Consequential state-mutation operation. "
            "CRITICAL: Requires explicit confirmation flag (confirmed=True) to execute. "
            "Unconfirmed requests are strictly blocked by the gatekeeper."
        ),
        input_schema=BookingInput,
        output_schema=MCPToolResponse,
        sensitivity="high",
        authorization_requirement="confirmed_booking",
        timeout_seconds=MCP_DEFAULT_TIMEOUT_SECONDS,
        audit_event="mcp_interview_booked",
        is_consequential=True,
        allows_state_mutation=True,
    ),
}


def get_tool_definition(tool_name: str) -> Optional[MCPToolDefinition]:
    """Look up an approved MCP tool definition by name."""
    return MCP_TOOL_REGISTRY.get(tool_name)


def is_tool_approved(tool_name: str) -> bool:
    """Returns True if the tool name is in the approved MCP registry."""
    return tool_name in MCP_TOOL_REGISTRY


def list_approved_tools() -> list[str]:
    """Returns list of all approved MCP tool names."""
    return list(MCP_TOOL_REGISTRY.keys())
