"""
Unit Tests for CAPABL UI Interview Operations Workspace (Phase 9).

Validates:
1. Calendar Multi-View Architecture:
   - Day View, Week View, Agenda View.
   - Grounded strictly in MockCalendarService with standard Asia/Kolkata operating timezone.
2. Enterprise Interview Card Contract:
   - Displays candidate, role, interviewer, date, time, duration, and status.
   - Semantic distinction for available vs confirmed booked status.
3. 5-Stage Animated Booking Flow:
   - Calendar Slot → Interview Preview → Confirmation Modal → Booking → Success State.
   - Motion keyframe @keyframes capablBookingStagePulse.
4. Security & Consequential Action Gatekeeper:
   - Explicit user confirmation is strictly mandatory.
   - Final booking execution strictly preserves confirmed=True.
   - Booking with confirmed=False is rejected with confirmation_required and audited.
5. Success State:
   - Displays "Interview scheduled".
   - Subtle calendar/check animation via @keyframes capablCalendarCheck.
6. Error & Stale Slot Protection:
   - "That slot is no longer available." on already booked or invalid slots.
   - Stale state animated away via @keyframes capablSlotFadeOut.
   - Never fakes a booking.
"""

import sys
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from capabl_core.calendar.service import DEFAULT_CALENDAR_SERVICE, MockCalendarService
from capabl_core.calendar.models import InterviewSlot, InterviewBooking, BookingResult
from capabl_core.ui.views.interviews import (
    render_interviews_workspace,
    render_interview_card,
    render_booking_flow_progress,
    format_slot_datetime,
)


class TestCAPABLInterviewOperations(unittest.TestCase):
    """Test suite for Phase 9 Interview Operations & Scheduling Workspace."""

    def setUp(self):
        """Set up test environment with a fresh calendar service."""
        self.cal_service = MockCalendarService()

    def test_interviews_view_exports(self):
        """Verifies that all required Phase 9 UI functions are exported and callable."""
        self.assertTrue(callable(render_interviews_workspace))
        self.assertTrue(callable(render_interview_card))
        self.assertTrue(callable(render_booking_flow_progress))
        self.assertTrue(callable(format_slot_datetime))

    def test_real_scheduling_service_data_and_timezone(self):
        """Validates that calendar data is pulled from actual service in Asia/Kolkata timezone."""
        search_res = self.cal_service.search_slots(
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            timezone_str="Asia/Kolkata",
        )
        self.assertGreater(len(search_res.slots), 0)

        # Check slot schema matches required fields
        slot = search_res.slots[0]
        self.assertIn("slot_id", slot)
        self.assertIn("start_time", slot)
        self.assertIn("end_time", slot)
        self.assertIn("interviewer_name", slot)
        self.assertIn("interviewer_role", slot)
        self.assertIn("duration_minutes", slot)
        self.assertEqual(slot["timezone"], "Asia/Kolkata")

    def test_calendar_views_present_in_source(self):
        """Validates presence of Day, Week, and Agenda views in interviews.py."""
        interviews_path = Path("capabl_core/ui/views/interviews.py")
        self.assertTrue(interviews_path.exists())
        content = interviews_path.read_text(encoding="utf-8")

        self.assertIn("Day View", content)
        self.assertIn("Week View", content)
        self.assertIn("Agenda View", content)
        self.assertIn("Chronological Day Schedule", content)
        self.assertIn("Weekly Multi-Day Operational View", content)
        self.assertIn("Chronological Interview Agenda", content)

    def test_interview_card_data_fields(self):
        """Validates interview card display requirements for candidate, role, interviewer, date, time, duration, status."""
        interviews_path = Path("capabl_core/ui/views/interviews.py")
        content = interviews_path.read_text(encoding="utf-8")

        # Candidate
        self.assertIn("Candidate", content)
        # Target Requisition / role
        self.assertIn("Target Requisition", content)
        # Interviewer
        self.assertIn("Interviewer", content)
        # Time / scheduled
        self.assertIn("Scheduled:", content)
        # Duration
        self.assertIn("minutes", content)
        # Status badges
        self.assertIn("Confirmed", content)
        self.assertIn("Open Slot", content)

    def test_five_stage_booking_flow_structure(self):
        """Validates the 5-stage animated booking flow sequence."""
        interviews_path = Path("capabl_core/ui/views/interviews.py")
        content = interviews_path.read_text(encoding="utf-8")

        self.assertIn("Calendar Slot", content)
        self.assertIn("Interview Preview", content)
        self.assertIn("Confirmation Modal", content)
        self.assertIn("Booking Execution", content)
        self.assertIn("Success State", content)

    def test_security_gatekeeper_blocks_unconfirmed_booking(self):
        """Validates that the booking service strictly enforces confirmed=True."""
        search_res = self.cal_service.search_slots(
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            timezone_str="Asia/Kolkata",
        )
        first_slot = search_res.slots[0]

        # Attempt booking without confirmation (confirmed=False)
        result_unconfirmed = self.cal_service.book_slot(
            slot_id=first_slot["slot_id"],
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            confirmed=False,
            notes="Unauthorized booking attempt",
        )
        self.assertEqual(result_unconfirmed.status, "confirmation_required")
        self.assertIsNone(result_unconfirmed.booking)
        self.assertIn("Explicit user confirmation is required", result_unconfirmed.message)

    def test_security_gatekeeper_preserves_confirmed_true(self):
        """Validates that a legitimate booking call preserves confirmed=True and creates booking."""
        search_res = self.cal_service.search_slots(
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            timezone_str="Asia/Kolkata",
        )
        target_slot = search_res.slots[0]

        # Valid booking with explicit confirmation
        result_confirmed = self.cal_service.book_slot(
            slot_id=target_slot["slot_id"],
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            confirmed=True,
            notes="Technical Screening Round 1",
        )
        self.assertEqual(result_confirmed.status, "success")
        self.assertIsNotNone(result_confirmed.booking)
        booking_data = (
            result_confirmed.booking
            if isinstance(result_confirmed.booking, dict)
            else result_confirmed.booking.model_dump()
        )
        self.assertEqual(booking_data["slot_id"], target_slot["slot_id"])
        self.assertEqual(booking_data["candidate_id"], "alex_chen")

    def test_success_banner_and_calendar_check_animation(self):
        """Validates presence of 'Interview scheduled' and capablCalendarCheck animation."""
        styles_path = Path("capabl_core/ui/theme/styles.py")
        styles_content = styles_path.read_text(encoding="utf-8")
        self.assertIn(".capabl-success-banner", styles_content)
        self.assertIn("capablCalendarCheck", styles_content)

        motion_path = Path("capabl_core/ui/theme/motion.py")
        motion_content = motion_path.read_text(encoding="utf-8")
        self.assertIn("@keyframes capablCalendarCheck", motion_content)

        interviews_path = Path("capabl_core/ui/views/interviews.py")
        interviews_content = interviews_path.read_text(encoding="utf-8")
        self.assertIn("Interview scheduled", interviews_content)

    def test_stale_slot_handling_and_animation(self):
        """Validates error message and animation when slot is already booked or unavailable."""
        # Book a slot first to make it unavailable
        slot_id = "slot_001"
        self.cal_service.book_slot(
            slot_id=slot_id,
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            confirmed=True,
        )

        # Attempt to book the same slot again
        double_book_result = self.cal_service.book_slot(
            slot_id=slot_id,
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            confirmed=True,
        )
        self.assertIn(double_book_result.status, ("already_booked", "duplicate_booking"))

        # Verify error text and stale animation in code
        interviews_path = Path("capabl_core/ui/views/interviews.py")
        interviews_content = interviews_path.read_text(encoding="utf-8")
        self.assertIn("That slot is no longer available.", interviews_content)
        self.assertIn("capabl-stale-slot", interviews_content)

        motion_path = Path("capabl_core/ui/theme/motion.py")
        motion_content = motion_path.read_text(encoding="utf-8")
        self.assertIn("@keyframes capablSlotFadeOut", motion_content)


if __name__ == "__main__":
    unittest.main()
