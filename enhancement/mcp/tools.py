"""
MCP Tool Adapters for CAPABL Core Services.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Architectural Invariant:
Business Logic -> Existing CAPABL Services -> Tool Contract -> MCP Adapter -> MCP Server.
MCP is strictly an interface boundary with zero duplicated business logic.
"""

import time
import logging
from typing import Optional, Dict, Any, Union

from capabl_core.evidence.service import EvidenceService
from capabl_core.calendar.service import MockCalendarService, DEFAULT_CALENDAR_SERVICE
from enhancement.security.audit_logger import DEFAULT_AUDIT_LOGGER
from enhancement.mcp.schemas import (
    CandidateEvidenceInput,
    JobEvidenceInput,
    PolicyEvidenceInput,
    InterviewSearchInput,
    BookingInput,
    MCPToolResponse,
)
from enhancement.mcp.security import (
    validate_safe_input,
    detect_and_neutralize_prompt_injection,
    verify_booking_confirmation,
    MCPSecurityError,
)

logger = logging.getLogger(__name__)


def _audit(event: str, status: str = "success", duration_sec: Optional[float] = None, **metadata: Any) -> None:
    """Helper to emit structured audit logs to DEFAULT_AUDIT_LOGGER."""
    duration_ms = round(duration_sec * 1000.0, 2) if duration_sec is not None else None
    DEFAULT_AUDIT_LOGGER.log_event(
        event=event,
        status=status,
        duration_ms=duration_ms,
        payload=metadata,
    )


class MCPToolAdapters:
    """
    Adapter layer bridging MCP tool invocations to underlying CAPABL services.
    Enforces argument validation, prompt injection neutralization, audit logging,
    and structured envelope responses.
    """

    def __init__(
        self,
        evidence_service: Optional[EvidenceService] = None,
        calendar_service: Optional[MockCalendarService] = None,
    ):
        self.evidence_service = evidence_service or EvidenceService()
        self.calendar_service = calendar_service or DEFAULT_CALENDAR_SERVICE

    def get_candidate_evidence(
        self,
        candidate_id: str,
        query: str,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """MCP adapter for retrieving candidate evidence strictly from their resume."""
        tool_name = "get_candidate_evidence"
        start_time = time.time()

        _audit(
            "mcp_tool_requested",
            status="requested",
            action=tool_name,
            component="mcp.adapter",
            candidate_id=candidate_id,
            query_length=len(query),
            top_k=top_k,
        )

        try:
            safe_cid = validate_safe_input(candidate_id, "candidate_id", max_length=100)
            safe_query = validate_safe_input(query, "query", max_length=500, allow_natural_language=True)
            is_injected, neutral_query = detect_and_neutralize_prompt_injection(safe_query)

            envelope = self.evidence_service.get_candidate_evidence(
                query=neutral_query,
                candidate_id=safe_cid,
                top_k=top_k,
            )

            evidence_items = [item.model_dump() for item in envelope.items]
            sources = list({item.source for item in envelope.items})
            response = MCPToolResponse.success(
                tool=tool_name,
                candidate_id=safe_cid,
                evidence=evidence_items,
                sources=sources,
                data={"items": evidence_items},
                message=f"Retrieved {len(evidence_items)} resume excerpts for candidate '{safe_cid}'.",
            )

            duration = round(time.time() - start_time, 4)
            _audit(
                "mcp_tool_executed",
                status="success",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                candidate_id=safe_cid,
                results_count=len(evidence_items),
                prompt_injection_flagged=is_injected,
            )
            return response.model_dump(mode="json")

        except MCPSecurityError as e:
            duration = round(time.time() - start_time, 4)
            _audit(
                "mcp_tool_blocked",
                status="blocked",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                error_code=e.error_code,
                reason=str(e),
            )
            return MCPToolResponse.blocked(
                tool=tool_name,
                message=str(e),
                error_code=e.error_code,
            ).model_dump(mode="json")

        except Exception as e:
            duration = round(time.time() - start_time, 4)
            logger.error("Error executing %s: %s", tool_name, str(e), exc_info=True)
            _audit(
                "mcp_tool_failed",
                status="failed",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                error_type=type(e).__name__,
            )
            return MCPToolResponse.error(
                tool=tool_name,
                message="Internal error retrieving candidate evidence.",
                error_code="INTERNAL_ERROR",
            ).model_dump(mode="json")

    def get_job_evidence(
        self,
        job_id: str,
        query: str,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """MCP adapter for retrieving job description requirements."""
        tool_name = "get_job_evidence"
        start_time = time.time()

        _audit(
            "mcp_tool_requested",
            status="requested",
            action=tool_name,
            component="mcp.adapter",
            job_id=job_id,
            query_length=len(query),
            top_k=top_k,
        )

        try:
            safe_jid = validate_safe_input(job_id, "job_id", max_length=100)
            safe_query = validate_safe_input(query, "query", max_length=500, allow_natural_language=True)
            is_injected, neutral_query = detect_and_neutralize_prompt_injection(safe_query)

            envelope = self.evidence_service.get_job_evidence(
                query=neutral_query,
                job_id=safe_jid,
                top_k=top_k,
            )

            evidence_items = [item.model_dump() for item in envelope.items]
            sources = list({item.source for item in envelope.items})
            response = MCPToolResponse.success(
                tool=tool_name,
                job_id=safe_jid,
                evidence=evidence_items,
                sources=sources,
                data={"items": evidence_items},
                message=f"Retrieved {len(evidence_items)} requirements excerpts for job '{safe_jid}'.",
            )

            duration = round(time.time() - start_time, 4)
            _audit(
                "mcp_tool_executed",
                status="success",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                job_id=safe_jid,
                results_count=len(evidence_items),
                prompt_injection_flagged=is_injected,
            )
            return response.model_dump(mode="json")

        except MCPSecurityError as e:
            duration = round(time.time() - start_time, 4)
            _audit(
                "mcp_tool_blocked",
                status="blocked",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                error_code=e.error_code,
                reason=str(e),
            )
            return MCPToolResponse.blocked(
                tool=tool_name,
                message=str(e),
                error_code=e.error_code,
            ).model_dump(mode="json")

        except Exception as e:
            duration = round(time.time() - start_time, 4)
            logger.error("Error executing %s: %s", tool_name, str(e), exc_info=True)
            _audit(
                "mcp_tool_failed",
                status="failed",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                error_type=type(e).__name__,
            )
            return MCPToolResponse.error(
                tool=tool_name,
                message="Internal error retrieving job evidence.",
                error_code="INTERNAL_ERROR",
            ).model_dump(mode="json")

    def get_policy_evidence(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """MCP adapter for retrieving company HR policies."""
        tool_name = "get_policy_evidence"
        start_time = time.time()

        _audit(
            "mcp_tool_requested",
            status="requested",
            action=tool_name,
            component="mcp.adapter",
            category=category,
            query_length=len(query),
            top_k=top_k,
        )

        try:
            safe_query = validate_safe_input(query, "query", max_length=500, allow_natural_language=True)
            safe_category = validate_safe_input(category, "category", max_length=100) if category else None
            is_injected, neutral_query = detect_and_neutralize_prompt_injection(safe_query)

            envelope = self.evidence_service.get_policy_evidence(
                query=neutral_query,
                category=safe_category,
                top_k=top_k,
            )

            evidence_items = [item.model_dump() for item in envelope.items]
            sources = list({item.source for item in envelope.items})
            response = MCPToolResponse.success(
                tool=tool_name,
                evidence=evidence_items,
                sources=sources,
                data={"items": evidence_items},
                message=f"Retrieved {len(evidence_items)} policy excerpts.",
            )

            duration = round(time.time() - start_time, 4)
            _audit(
                "mcp_tool_executed",
                status="success",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                category=safe_category,
                results_count=len(evidence_items),
                prompt_injection_flagged=is_injected,
            )
            return response.model_dump(mode="json")

        except MCPSecurityError as e:
            duration = round(time.time() - start_time, 4)
            _audit(
                "mcp_tool_blocked",
                status="blocked",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                error_code=e.error_code,
                reason=str(e),
            )
            return MCPToolResponse.blocked(
                tool=tool_name,
                message=str(e),
                error_code=e.error_code,
            ).model_dump(mode="json")

        except Exception as e:
            duration = round(time.time() - start_time, 4)
            logger.error("Error executing %s: %s", tool_name, str(e), exc_info=True)
            _audit(
                "mcp_tool_failed",
                status="failed",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                error_type=type(e).__name__,
            )
            return MCPToolResponse.error(
                tool=tool_name,
                message="Internal error retrieving policy evidence.",
                error_code="INTERNAL_ERROR",
            ).model_dump(mode="json")

    def search_interview_slots(
        self,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        timezone: Optional[str] = "Asia/Kolkata",
    ) -> Dict[str, Any]:
        """MCP adapter for searching mock interview slots."""
        tool_name = "search_interview_slots"
        start_time = time.time()

        _audit(
            "mcp_tool_requested",
            status="requested",
            action=tool_name,
            component="mcp.adapter",
            candidate_id=candidate_id,
            job_id=job_id,
            date=date,
        )

        try:
            safe_cid = validate_safe_input(candidate_id, "candidate_id", max_length=100) if candidate_id else None
            safe_jid = validate_safe_input(job_id, "job_id", max_length=100) if job_id else None

            result = self.calendar_service.search_slots(
                candidate_id=safe_cid,
                job_id=safe_jid,
                date=date,
                start_date=start_date,
                end_date=end_date,
                duration_minutes=duration_minutes,
                timezone_str=timezone or "Asia/Kolkata",
            )

            result_dict = result.model_dump(mode="json")
            response = MCPToolResponse.success(
                tool=tool_name,
                candidate_id=safe_cid,
                job_id=safe_jid,
                data=result_dict,
                message=f"Found {result.total_slots_found} available interview slots.",
            )

            duration = round(time.time() - start_time, 4)
            _audit(
                "mcp_tool_executed",
                status="success",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                available_count=result.total_slots_found,
            )
            return response.model_dump(mode="json")

        except MCPSecurityError as e:
            duration = round(time.time() - start_time, 4)
            _audit(
                "mcp_tool_blocked",
                status="blocked",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                error_code=e.error_code,
                reason=str(e),
            )
            return MCPToolResponse.blocked(
                tool=tool_name,
                message=str(e),
                error_code=e.error_code,
            ).model_dump(mode="json")

        except Exception as e:
            duration = round(time.time() - start_time, 4)
            logger.error("Error executing %s: %s", tool_name, str(e), exc_info=True)
            _audit(
                "mcp_tool_failed",
                status="failed",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                error_type=type(e).__name__,
            )
            return MCPToolResponse.error(
                tool=tool_name,
                message="Internal error searching interview slots.",
                error_code="INTERNAL_ERROR",
            ).model_dump(mode="json")

    def book_interview(
        self,
        slot_id: str,
        candidate_id: str,
        job_id: str,
        confirmed: bool = False,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        MCP adapter for booking an interview slot.
        Consequential state-changing operation: Gatekeeper strictly requires confirmed=True.
        """
        tool_name = "book_interview"
        start_time = time.time()

        _audit(
            "mcp_tool_requested",
            status="requested",
            action=tool_name,
            component="mcp.adapter",
            slot_id=slot_id,
            candidate_id=candidate_id,
            job_id=job_id,
            confirmed=confirmed,
        )

        try:
            safe_sid = validate_safe_input(slot_id, "slot_id", max_length=100)
            safe_cid = validate_safe_input(candidate_id, "candidate_id", max_length=100)
            safe_jid = validate_safe_input(job_id, "job_id", max_length=100)
            safe_notes = validate_safe_input(notes, "notes", max_length=1000, allow_natural_language=True) if notes else None

            # Consequential Security Gate: MUST be confirmed
            verify_booking_confirmation(confirmed=confirmed, slot_id=safe_sid, candidate_id=safe_cid)

            # Invoke calendar service
            result = self.calendar_service.book_slot(
                slot_id=safe_sid,
                candidate_id=safe_cid,
                job_id=safe_jid,
                confirmed=confirmed,
                notes=safe_notes,
            )

            result_dict = result.model_dump(mode="json")

            if result.status == "success":
                response = MCPToolResponse.success(
                    tool=tool_name,
                    candidate_id=safe_cid,
                    job_id=safe_jid,
                    data=result_dict,
                    message=f"Interview booked successfully for slot '{safe_sid}'.",
                )
                status_str = "success"
            else:
                response = MCPToolResponse.blocked(
                    tool=tool_name,
                    message=result.message or "Booking could not be confirmed.",
                    error_code="BOOKING_FAILED",
                    data=result_dict,
                )
                status_str = "blocked"

            duration = round(time.time() - start_time, 4)
            _audit(
                "mcp_tool_executed",
                status=status_str,
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                slot_id=safe_sid,
                candidate_id=safe_cid,
            )
            return response.model_dump(mode="json")

        except MCPSecurityError as e:
            duration = round(time.time() - start_time, 4)
            return MCPToolResponse.blocked(
                tool=tool_name,
                message=str(e),
                error_code=e.error_code,
            ).model_dump(mode="json")

        except Exception as e:
            duration = round(time.time() - start_time, 4)
            logger.error("Error executing %s: %s", tool_name, str(e), exc_info=True)
            _audit(
                "mcp_tool_failed",
                status="failed",
                duration_sec=duration,
                action=tool_name,
                component="mcp.adapter",
                error_type=type(e).__name__,
            )
            return MCPToolResponse.error(
                tool=tool_name,
                message="Internal error booking interview.",
                error_code="INTERNAL_ERROR",
            ).model_dump(mode="json")
