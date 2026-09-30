"""
FastMCP Server for CAPABL Recruitment Intelligence Agent.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Architectural Boundary:
- Exposes strictly approved tools
- Validates typed arguments
- Returns structured results
- Never exposes secrets, raw internals, or bypasses authorization
- Produces structured audit events
"""

import sys
import logging
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP

from capabl_core.evidence.service import EvidenceService
from capabl_core.calendar.service import MockCalendarService, DEFAULT_CALENDAR_SERVICE
from enhancement.mcp.tools import MCPToolAdapters
from enhancement.mcp.registry import MCP_TOOL_REGISTRY, is_tool_approved

logger = logging.getLogger(__name__)


def create_mcp_server(
    evidence_service: Optional[EvidenceService] = None,
    calendar_service: Optional[MockCalendarService] = None,
) -> FastMCP:
    """
    Factory creating a configured FastMCP server exposing approved CAPABL tools.
    Supports dependency injection for hermetic unit testing.
    """
    adapters = MCPToolAdapters(
        evidence_service=evidence_service,
        calendar_service=calendar_service,
    )

    server = FastMCP(
        name="capabl_recruitment_mcp",
        instructions=(
            "CAPABL Recruitment Intelligence MCP Server. Provides read-only candidate, "
            "job, and policy evidence retrieval, plus confirmation-gated interview scheduling."
        ),
    )

    # 1. Candidate Evidence Tool (Read-only)
    @server.tool(
        name="get_candidate_evidence",
        description=MCP_TOOL_REGISTRY["get_candidate_evidence"].description,
    )
    def get_candidate_evidence(
        candidate_id: str,
        query: str,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        return adapters.get_candidate_evidence(
            candidate_id=candidate_id,
            query=query,
            top_k=top_k,
        )

    # 2. Job Evidence Tool (Read-only)
    @server.tool(
        name="get_job_evidence",
        description=MCP_TOOL_REGISTRY["get_job_evidence"].description,
    )
    def get_job_evidence(
        job_id: str,
        query: str,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        return adapters.get_job_evidence(
            job_id=job_id,
            query=query,
            top_k=top_k,
        )

    # 3. Policy Evidence Tool (Read-only)
    @server.tool(
        name="get_policy_evidence",
        description=MCP_TOOL_REGISTRY["get_policy_evidence"].description,
    )
    def get_policy_evidence(
        query: str,
        category: Optional[str] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        return adapters.get_policy_evidence(
            query=query,
            category=category,
            top_k=top_k,
        )

    # 4. Search Interview Slots (Read-only)
    @server.tool(
        name="search_interview_slots",
        description=MCP_TOOL_REGISTRY["search_interview_slots"].description,
    )
    def search_interview_slots(
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        timezone: Optional[str] = "Asia/Kolkata",
    ) -> Dict[str, Any]:
        return adapters.search_interview_slots(
            candidate_id=candidate_id,
            job_id=job_id,
            date=date,
            start_date=start_date,
            end_date=end_date,
            duration_minutes=duration_minutes,
            timezone=timezone,
        )

    # 5. Book Interview Slot (Consequential, Requires Confirmation)
    @server.tool(
        name="book_interview",
        description=MCP_TOOL_REGISTRY["book_interview"].description,
    )
    def book_interview(
        slot_id: str,
        candidate_id: str,
        job_id: str,
        confirmed: bool = False,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        return adapters.book_interview(
            slot_id=slot_id,
            candidate_id=candidate_id,
            job_id=job_id,
            confirmed=confirmed,
            notes=notes,
        )

    return server


# Global singleton instance
mcp_server: FastMCP = create_mcp_server()


if __name__ == "__main__":
    # Run the FastMCP server over stdio when executed directly
    logger.info("Starting CAPABL FastMCP server on stdio...")
    mcp_server.run()
