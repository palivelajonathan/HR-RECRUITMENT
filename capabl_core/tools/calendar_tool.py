"""
Mock Interview Calendar Tools for LangChain Agent.

CAPABL Track 6 Requirement:
- Interview Slot Lookup / Booking Tool.
- Non-consequential query tool: `search_interview_slots`.
- Consequential state-mutation tool: `book_interview` requiring explicit user confirmation.
- Timezone-aware scheduling (Asia/Kolkata standard).
- Prevention of duplicate bookings, invalid slots, and candidate/job mismatches.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool, BaseTool

from capabl_core.calendar.models import SlotSearchResult, BookingResult
from capabl_core.calendar.service import MockCalendarService, DEFAULT_CALENDAR_SERVICE


class SearchSlotsInput(BaseModel):
    """Input schema for searching available interview slots."""
    candidate_id: Optional[str] = Field(
        default=None,
        description="Candidate ID to filter available slots for (e.g. 'alex_chen').",
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Job ID to filter available slots for (e.g. 'jd_backend_lead_2026').",
    )
    date: Optional[str] = Field(
        default=None,
        description="Specific target date in YYYY-MM-DD format (e.g. '2026-09-29').",
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Optional start date range filter in YYYY-MM-DD format.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Optional end date range filter in YYYY-MM-DD format.",
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Filter by slot duration in minutes (e.g. 30, 45, 60).",
    )
    timezone: Optional[str] = Field(
        default="Asia/Kolkata",
        description="Target timezone string identifier (defaults to 'Asia/Kolkata').",
    )


class BookInterviewInput(BaseModel):
    """Input schema for booking an interview slot."""
    slot_id: str = Field(
        ...,
        description="Unique slot identifier to book (e.g. 'slot_001').",
    )
    candidate_id: str = Field(
        ...,
        description="Unique candidate identifier (e.g. 'alex_chen').",
    )
    job_id: str = Field(
        ...,
        description="Unique job identifier (e.g. 'jd_backend_lead_2026').",
    )
    confirmed: bool = Field(
        default=False,
        description=(
            "Explicit user confirmation flag. Must be explicitly True. "
            "If False, booking is rejected with status 'confirmation_required'."
        ),
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional recruiter notes for the interview session.",
    )


# Backward compatibility aliases
CheckAvailabilityInputSchema = SearchSlotsInput
BookInterviewInputSchema = BookInterviewInput


def create_search_slots_tool(calendar_service: Optional[MockCalendarService] = None) -> BaseTool:
    """Factory creating an isolated search_interview_slots LangChain tool."""
    service = calendar_service or DEFAULT_CALENDAR_SERVICE

    @tool("search_interview_slots", args_schema=SearchSlotsInput)
    def search_interview_slots_instance(
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        timezone: Optional[str] = "Asia/Kolkata",
    ) -> Dict[str, Any]:
        """
        Search available interview slots in the mock calendar.
        Deterministic and non-consequential query tool.
        Filters by candidate, job, target date/range, duration, and timezone.
        """
        result: SlotSearchResult = service.search_slots(
            candidate_id=candidate_id,
            job_id=job_id,
            date=date,
            start_date=start_date,
            end_date=end_date,
            duration_minutes=duration_minutes,
            timezone_str=timezone or "Asia/Kolkata",
        )
        return result.model_dump(mode="json")

    return search_interview_slots_instance


def create_book_interview_tool(calendar_service: Optional[MockCalendarService] = None) -> BaseTool:
    """Factory creating an isolated book_interview LangChain tool."""
    service = calendar_service or DEFAULT_CALENDAR_SERVICE

    @tool("book_interview", args_schema=BookInterviewInput)
    def book_interview_instance(
        slot_id: str,
        candidate_id: str,
        job_id: str,
        confirmed: bool = False,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Books an interview slot into the mock calendar.
        Consequential state-mutation operation requiring explicit user confirmation.
        Enforces validation: confirmed=True, slot existence, candidate match, job match,
        and duplicate booking prevention.
        """
        result: BookingResult = service.book_slot(
            slot_id=slot_id,
            candidate_id=candidate_id,
            job_id=job_id,
            confirmed=confirmed,
            notes=notes,
        )
        return result.model_dump(mode="json")

    return book_interview_instance


# Default singleton instances bound to DEFAULT_CALENDAR_SERVICE
search_interview_slots = create_search_slots_tool()
book_interview = create_book_interview_tool()

__all__ = [
    "SearchSlotsInput",
    "BookInterviewInput",
    "CheckAvailabilityInputSchema",
    "BookInterviewInputSchema",
    "search_interview_slots",
    "book_interview",
    "create_search_slots_tool",
    "create_book_interview_tool",
    "MockCalendarService",
]
