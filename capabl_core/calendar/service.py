"""
Deterministic Mock Interview Calendar Service.

CAPABL Requirement:
- Deterministic mock interview calendar.
- Realistic interview events and availability periods.
- Timezone-aware datetime handling (Asia/Kolkata standard).
- Prevention of duplicate bookings and invalid/mismatched slots.
- Explicit confirmation boundary enforcement before state mutation.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional, Any
from copy import deepcopy

from capabl_core.calendar.models import (
    InterviewSlot,
    InterviewBooking,
    SlotSearchResult,
    BookingResult,
)


def create_initial_mock_slots() -> List[InterviewSlot]:
    """Generates a realistic deterministic set of interview slots in Asia/Kolkata."""
    kolkata_tz = ZoneInfo("Asia/Kolkata")
    return [
        InterviewSlot(
            slot_id="slot_001",
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            start_time=datetime(2026, 9, 29, 10, 0, tzinfo=kolkata_tz),
            end_time=datetime(2026, 9, 29, 10, 30, tzinfo=kolkata_tz),
            timezone="Asia/Kolkata",
            duration_minutes=30,
            status="available",
            interviewer_name="Vikram Malhotra",
            interviewer_role="Engineering Director",
        ),
        InterviewSlot(
            slot_id="slot_002",
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            start_time=datetime(2026, 9, 29, 11, 30, tzinfo=kolkata_tz),
            end_time=datetime(2026, 9, 29, 12, 0, tzinfo=kolkata_tz),
            timezone="Asia/Kolkata",
            duration_minutes=30,
            status="available",
            interviewer_name="Vikram Malhotra",
            interviewer_role="Engineering Director",
        ),
        InterviewSlot(
            slot_id="slot_003",
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            start_time=datetime(2026, 9, 29, 14, 0, tzinfo=kolkata_tz),
            end_time=datetime(2026, 9, 29, 15, 0, tzinfo=kolkata_tz),
            timezone="Asia/Kolkata",
            duration_minutes=60,
            status="available",
            interviewer_name="Vikram Malhotra",
            interviewer_role="Engineering Director",
        ),
        InterviewSlot(
            slot_id="slot_004",
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            start_time=datetime(2026, 9, 30, 10, 30, tzinfo=kolkata_tz),
            end_time=datetime(2026, 9, 30, 11, 0, tzinfo=kolkata_tz),
            timezone="Asia/Kolkata",
            duration_minutes=30,
            status="available",
            interviewer_name="Vikram Malhotra",
            interviewer_role="Engineering Director",
        ),
        InterviewSlot(
            slot_id="slot_005",
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            start_time=datetime(2026, 9, 30, 16, 0, tzinfo=kolkata_tz),
            end_time=datetime(2026, 9, 30, 16, 45, tzinfo=kolkata_tz),
            timezone="Asia/Kolkata",
            duration_minutes=45,
            status="available",
            interviewer_name="Sneha Rao",
            interviewer_role="HR Business Partner",
        ),
        InterviewSlot(
            slot_id="slot_006",
            candidate_id="priya_sharma",
            job_id="jd_backend_lead_2026",
            start_time=datetime(2026, 9, 29, 11, 0, tzinfo=kolkata_tz),
            end_time=datetime(2026, 9, 29, 11, 30, tzinfo=kolkata_tz),
            timezone="Asia/Kolkata",
            duration_minutes=30,
            status="available",
            interviewer_name="Vikram Malhotra",
            interviewer_role="Engineering Director",
        ),
        InterviewSlot(
            slot_id="slot_007",
            candidate_id="priya_sharma",
            job_id="jd_backend_lead_2026",
            start_time=datetime(2026, 10, 1, 15, 0, tzinfo=kolkata_tz),
            end_time=datetime(2026, 10, 1, 15, 30, tzinfo=kolkata_tz),
            timezone="Asia/Kolkata",
            duration_minutes=30,
            status="available",
            interviewer_name="Sneha Rao",
            interviewer_role="HR Business Partner",
        ),
        InterviewSlot(
            slot_id="slot_008",
            candidate_id="david_kim",
            job_id="jd_backend_lead_2026",
            start_time=datetime(2026, 10, 2, 10, 0, tzinfo=kolkata_tz),
            end_time=datetime(2026, 10, 2, 10, 30, tzinfo=kolkata_tz),
            timezone="Asia/Kolkata",
            duration_minutes=30,
            status="available",
            interviewer_name="Vikram Malhotra",
            interviewer_role="Engineering Director",
        ),
    ]


class MockCalendarService:
    """
    In-memory deterministic mock calendar service.
    
    Serves as the single source of truth for interview slot availability and booking state.
    Provides strict validation against duplicate bookings, slot mismatch, and unconfirmed actions.
    """

    def __init__(self, initial_slots: Optional[List[InterviewSlot]] = None):
        self._slots: Dict[str, InterviewSlot] = {}
        self._bookings: Dict[str, InterviewBooking] = {}
        self._initial_slots = initial_slots if initial_slots is not None else create_initial_mock_slots()
        self.reset()

    def reset(self) -> None:
        """Resets the calendar to its initial seeded state and clears all bookings."""
        self._slots.clear()
        self._bookings.clear()
        for slot in self._initial_slots:
            self._slots[slot.slot_id] = deepcopy(slot)

    def seed_slots(self, slots: List[InterviewSlot]) -> None:
        """Allows test suites to seed custom slots."""
        self._slots.clear()
        self._bookings.clear()
        for slot in slots:
            self._slots[slot.slot_id] = deepcopy(slot)

    def search_slots(
        self,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        timezone_str: str = "Asia/Kolkata",
    ) -> SlotSearchResult:
        """
        Queries available interview slots with deterministic multi-attribute filtering.
        
        Args:
            candidate_id: Optional target candidate ID.
            job_id: Optional target job ID.
            date: Optional exact date string (YYYY-MM-DD).
            start_date: Optional range start date (YYYY-MM-DD).
            end_date: Optional range end date (YYYY-MM-DD).
            duration_minutes: Optional duration filter in minutes.
            timezone_str: Target timezone string identifier (default 'Asia/Kolkata').
            
        Returns:
            SlotSearchResult with matching available slots.
        """
        try:
            target_tz = ZoneInfo(timezone_str)
        except Exception:
            target_tz = ZoneInfo("Asia/Kolkata")
            timezone_str = "Asia/Kolkata"

        matching_slots: List[Dict[str, Any]] = []

        for slot in self._slots.values():
            # Only consider available slots
            if slot.status != "available" or slot.slot_id in self._bookings:
                continue

            # Candidate filter
            if candidate_id and slot.candidate_id.lower() != candidate_id.strip().lower():
                continue

            # Job filter
            if job_id and slot.job_id.lower() != job_id.strip().lower():
                continue

            # Duration filter
            if duration_minutes is not None and slot.duration_minutes != duration_minutes:
                continue

            # Timezone localized slot start
            local_start = slot.start_time.astimezone(target_tz)
            local_end = slot.end_time.astimezone(target_tz)
            local_date_str = local_start.strftime("%Y-%m-%d")

            # Date exact filter
            if date and local_date_str != date.strip():
                continue

            # Date range filters
            if start_date and local_date_str < start_date.strip():
                continue
            if end_date and local_date_str > end_date.strip():
                continue

            matching_slots.append({
                "slot_id": slot.slot_id,
                "candidate_id": slot.candidate_id,
                "job_id": slot.job_id,
                "start_time": local_start.isoformat(),
                "end_time": local_end.isoformat(),
                "display_time": f"{local_start.strftime('%A, %d %B %Y %I:%M %p')} - {local_end.strftime('%I:%M %p')} {timezone_str}",
                "timezone": timezone_str,
                "duration_minutes": slot.duration_minutes,
                "status": slot.status,
                "interviewer_name": slot.interviewer_name,
                "interviewer_role": slot.interviewer_role,
            })

        # Sort by start_time for deterministic order
        matching_slots.sort(key=lambda s: s["start_time"])

        if not matching_slots:
            return SlotSearchResult(
                status="no_slots",
                candidate_id=candidate_id,
                job_id=job_id,
                timezone=timezone_str,
                total_slots_found=0,
                slots=[],
                message="No available interview slots matching the specified criteria.",
            )

        return SlotSearchResult(
            status="success",
            candidate_id=candidate_id,
            job_id=job_id,
            timezone=timezone_str,
            total_slots_found=len(matching_slots),
            slots=matching_slots,
            message=f"Found {len(matching_slots)} available interview slot(s).",
        )

    def book_slot(
        self,
        slot_id: str,
        candidate_id: str,
        job_id: str,
        confirmed: bool = False,
        notes: Optional[str] = None,
    ) -> BookingResult:
        """
        Atomically validates and books an interview slot into the calendar.
        
        Enforces strict safety boundary:
        1. Rejects unconfirmed booking requests (confirmed=False).
        2. Rejects nonexistent slots (invalid_slot).
        3. Rejects candidate mismatches (candidate_mismatch).
        4. Rejects job mismatches (job_mismatch).
        5. Rejects already booked slots (already_booked).
        
        Args:
            slot_id: Slot identifier to book.
            candidate_id: Candidate identifier.
            job_id: Job identifier.
            confirmed: Explicit confirmation flag. Must be True to execute booking.
            notes: Optional booking notes.
            
        Returns:
            BookingResult with outcome status and booking record if confirmed.
        """
        clean_slot_id = slot_id.strip() if slot_id else ""
        clean_candidate_id = candidate_id.strip().lower() if candidate_id else ""
        clean_job_id = job_id.strip().lower() if job_id else ""

        # 1. Consequential Action Safety Gate: Explicit user confirmation required
        if not confirmed:
            return BookingResult(
                status="confirmation_required",
                message="Explicit user confirmation is required before booking can be executed.",
                slot_id=clean_slot_id,
                candidate_id=clean_candidate_id,
                job_id=clean_job_id,
            )

        # 2. Existence check
        if clean_slot_id not in self._slots:
            return BookingResult(
                status="invalid_slot",
                message=f"Interview slot '{clean_slot_id}' does not exist in calendar.",
                slot_id=clean_slot_id,
                candidate_id=clean_candidate_id,
                job_id=clean_job_id,
            )

        slot = self._slots[clean_slot_id]

        # 3. Candidate validation
        if slot.candidate_id.lower() != clean_candidate_id:
            return BookingResult(
                status="candidate_mismatch",
                message=(
                    f"Slot '{clean_slot_id}' is configured for candidate '{slot.candidate_id}', "
                    f"not '{clean_candidate_id}'."
                ),
                slot_id=clean_slot_id,
                candidate_id=clean_candidate_id,
                job_id=clean_job_id,
            )

        # 4. Job validation
        if slot.job_id.lower() != clean_job_id:
            return BookingResult(
                status="job_mismatch",
                message=(
                    f"Slot '{clean_slot_id}' is configured for job '{slot.job_id}', "
                    f"not '{clean_job_id}'."
                ),
                slot_id=clean_slot_id,
                candidate_id=clean_candidate_id,
                job_id=clean_job_id,
            )

        # 5. Availability & double-booking check
        if slot.status != "available" or clean_slot_id in self._bookings:
            return BookingResult(
                status="already_booked",
                message=f"Slot '{clean_slot_id}' is already booked and cannot be double-booked.",
                slot_id=clean_slot_id,
                candidate_id=clean_candidate_id,
                job_id=clean_job_id,
            )

        # 6. Atomic state mutation on successful validation
        tz = ZoneInfo(slot.timezone)
        now_tz = datetime.now(tz)
        booking_id = f"book_{clean_slot_id}_{int(now_tz.timestamp())}"

        booking = InterviewBooking(
            booking_id=booking_id,
            slot_id=clean_slot_id,
            candidate_id=slot.candidate_id,
            job_id=slot.job_id,
            start_time=slot.start_time,
            end_time=slot.end_time,
            timezone=slot.timezone,
            status="confirmed",
            created_at=now_tz,
            notes=notes,
        )

        # Update slot status
        slot.status = "booked"
        self._bookings[clean_slot_id] = booking

        formatted_time = (
            f"{slot.start_time.strftime('%A, %d %B %Y')} from "
            f"{slot.start_time.strftime('%I:%M %p')} to {slot.end_time.strftime('%I:%M %p %Z')}"
        )

        return BookingResult(
            status="success",
            message=(
                f"Interview successfully confirmed and booked for {slot.candidate_id} "
                f"({formatted_time}) with {slot.interviewer_name} ({slot.interviewer_role}). "
                f"Booking ID: {booking_id}."
            ),
            booking=booking.model_dump(mode="json"),
            slot_id=clean_slot_id,
            candidate_id=slot.candidate_id,
            job_id=slot.job_id,
        )

    def add_slot(
        self,
        date_str: str,
        start_time_str: str,
        end_time_str: str,
        interviewer_name: str,
        interviewer_role: str = "Recruitment Panel",
        candidate_id: str = "",
        job_id: str = "",
        timezone_str: str = "Asia/Kolkata",
    ) -> Dict[str, Any]:
        """
        Adds a new interview availability slot created by a recruiter.

        Args:
            date_str: Date in YYYY-MM-DD format.
            start_time_str: Start time in HH:MM (24h) format.
            end_time_str: End time in HH:MM (24h) format.
            interviewer_name: Name of the interviewer.
            interviewer_role: Role/title of the interviewer.
            candidate_id: Optional candidate ID (empty = open slot).
            job_id: Optional job ID (empty = general).
            timezone_str: Timezone identifier.

        Returns:
            Dict with status and slot details.
        """
        try:
            tz = ZoneInfo(timezone_str)
        except Exception:
            return {"status": "error", "message": f"Invalid timezone: {timezone_str}"}

        # Parse date and times
        try:
            year, month, day = map(int, date_str.split("-"))
            s_hour, s_min = map(int, start_time_str.split(":"))
            e_hour, e_min = map(int, end_time_str.split(":"))
        except (ValueError, AttributeError):
            return {"status": "error", "message": "Invalid date or time format. Use YYYY-MM-DD and HH:MM."}

        try:
            start_dt = datetime(year, month, day, s_hour, s_min, tzinfo=tz)
            end_dt = datetime(year, month, day, e_hour, e_min, tzinfo=tz)
        except ValueError as exc:
            return {"status": "error", "message": f"Invalid datetime: {exc}"}

        # Validation: end must be after start
        if end_dt <= start_dt:
            return {"status": "error", "message": "End time must be after start time."}

        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

        # Check overlap for same interviewer
        for existing in self._slots.values():
            if existing.interviewer_name and existing.interviewer_name.lower() == interviewer_name.strip().lower():
                if existing.status != "cancelled":
                    if start_dt < existing.end_time and end_dt > existing.start_time:
                        return {
                            "status": "error",
                            "message": (
                                f"Overlapping slot exists for {interviewer_name}: "
                                f"{existing.slot_id} ({existing.start_time.strftime('%H:%M')}-{existing.end_time.strftime('%H:%M')})"
                            ),
                        }

        # Generate unique slot ID
        slot_count = len(self._slots) + 1
        slot_id = f"slot_{slot_count:03d}"
        while slot_id in self._slots:
            slot_count += 1
            slot_id = f"slot_{slot_count:03d}"

        new_slot = InterviewSlot(
            slot_id=slot_id,
            candidate_id=candidate_id or "unassigned",
            job_id=job_id or "general",
            start_time=start_dt,
            end_time=end_dt,
            timezone=timezone_str,
            duration_minutes=duration_minutes,
            status="available",
            interviewer_name=interviewer_name.strip(),
            interviewer_role=interviewer_role.strip(),
        )

        self._slots[slot_id] = new_slot

        return {
            "status": "success",
            "slot_id": slot_id,
            "message": (
                f"Interview slot {slot_id} created: {interviewer_name} on "
                f"{date_str} {start_time_str}-{end_time_str} ({timezone_str})"
            ),
            "slot": new_slot.model_dump(mode="json"),
        }

    def get_all_slots(self) -> List[Dict[str, Any]]:
        """Returns all slots with their current status."""
        result = []
        for slot in sorted(self._slots.values(), key=lambda s: s.start_time):
            tz = ZoneInfo(slot.timezone)
            local_start = slot.start_time.astimezone(tz)
            local_end = slot.end_time.astimezone(tz)
            is_booked = slot.slot_id in self._bookings
            result.append({
                "slot_id": slot.slot_id,
                "candidate_id": slot.candidate_id,
                "job_id": slot.job_id,
                "start_time": local_start.isoformat(),
                "end_time": local_end.isoformat(),
                "date_str": local_start.strftime("%Y-%m-%d"),
                "date_label": local_start.strftime("%a, %d %b %Y"),
                "time_label": f"{local_start.strftime('%I:%M %p')} – {local_end.strftime('%I:%M %p')}",
                "timezone": slot.timezone,
                "duration_minutes": slot.duration_minutes,
                "status": "booked" if is_booked else slot.status,
                "interviewer_name": slot.interviewer_name or "TBD",
                "interviewer_role": slot.interviewer_role or "",
                "display_time": f"{local_start.strftime('%A, %d %B %Y %I:%M %p')} – {local_end.strftime('%I:%M %p')} {slot.timezone}",
            })
        return result

    def get_booking(self, slot_id: str) -> Optional[InterviewBooking]:
        """Retrieves booking record by slot ID."""
        return self._bookings.get(slot_id)

    def get_slot(self, slot_id: str) -> Optional[InterviewSlot]:
        """Retrieves slot by slot ID."""
        return self._slots.get(slot_id)


# Global singleton instance for runtime and default tool binding
DEFAULT_CALENDAR_SERVICE = MockCalendarService()
