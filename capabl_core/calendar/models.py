"""
Domain models for the Mock Interview Calendar.

CAPABL Requirement:
- Timezone-aware datetime representation (Asia/Kolkata standard).
- Structured Pydantic models for slots, bookings, and calendar events.
- Strict validation preventing naive datetimes internally.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class CalendarEvent(BaseModel):
    """Base calendar event representation."""
    event_id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Title of the calendar event")
    start_time: datetime = Field(..., description="Timezone-aware event start datetime")
    end_time: datetime = Field(..., description="Timezone-aware event end datetime")
    timezone: str = Field(default="Asia/Kolkata", description="Timezone string identifier")
    description: Optional[str] = Field(default=None, description="Event description or notes")

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("All calendar event datetimes must be timezone-aware")
        return v


class InterviewSlot(BaseModel):
    """Represents an interview availability window."""
    slot_id: str = Field(..., description="Unique slot identifier (e.g., 'slot_001')")
    candidate_id: str = Field(..., description="Target candidate identifier (e.g., 'alex_chen')")
    job_id: str = Field(..., description="Job identifier for interview context (e.g., 'jd_backend_lead_2026')")
    start_time: datetime = Field(..., description="Timezone-aware slot start datetime")
    end_time: datetime = Field(..., description="Timezone-aware slot end datetime")
    timezone: str = Field(default="Asia/Kolkata", description="Timezone identifier")
    duration_minutes: int = Field(default=30, description="Duration of the slot in minutes")
    status: Literal["available", "booked", "cancelled"] = Field(default="available", description="Slot availability status")
    interviewer_name: Optional[str] = Field(default=None, description="Assigned interviewer name")
    interviewer_role: Optional[str] = Field(default=None, description="Interviewer job title or role")

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("All interview slot datetimes must be timezone-aware")
        return v


class InterviewBooking(BaseModel):
    """Represents a confirmed interview booking."""
    booking_id: str = Field(..., description="Unique booking record identifier")
    slot_id: str = Field(..., description="Slot identifier that was booked")
    candidate_id: str = Field(..., description="Candidate identifier")
    job_id: str = Field(..., description="Job description identifier")
    start_time: datetime = Field(..., description="Timezone-aware scheduled start datetime")
    end_time: datetime = Field(..., description="Timezone-aware scheduled end datetime")
    timezone: str = Field(default="Asia/Kolkata", description="Booking timezone identifier")
    status: Literal["confirmed", "cancelled"] = Field(default="confirmed", description="Booking status")
    created_at: datetime = Field(..., description="Timezone-aware booking timestamp")
    notes: Optional[str] = Field(default=None, description="Booking notes or confirmation metadata")

    @field_validator("start_time", "end_time", "created_at")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("All interview booking datetimes must be timezone-aware")
        return v


class SlotSearchResult(BaseModel):
    """Structured response contract for interview slot searches."""
    status: Literal["success", "no_slots", "invalid_request", "error"] = Field(
        default="success", description="Search outcome status"
    )
    candidate_id: Optional[str] = Field(default=None, description="Candidate queried")
    job_id: Optional[str] = Field(default=None, description="Job queried")
    timezone: str = Field(default="Asia/Kolkata", description="Timezone used for search")
    total_slots_found: int = Field(default=0, description="Total matching slots found")
    slots: List[Dict[str, Any]] = Field(default_factory=list, description="List of matching available slots")
    message: Optional[str] = Field(default=None, description="Descriptive status message")


class BookingResult(BaseModel):
    """Structured response contract for interview booking attempts."""
    status: Literal[
        "success",
        "confirmation_required",
        "invalid_slot",
        "already_booked",
        "candidate_mismatch",
        "job_mismatch",
        "error",
    ] = Field(..., description="Deterministic booking outcome status")
    message: str = Field(..., description="Human-readable result explanation")
    booking: Optional[Dict[str, Any]] = Field(default=None, description="Booking details if successfully confirmed")
    slot_id: Optional[str] = Field(default=None, description="Target slot identifier")
    candidate_id: Optional[str] = Field(default=None, description="Target candidate identifier")
    job_id: Optional[str] = Field(default=None, description="Target job identifier")
