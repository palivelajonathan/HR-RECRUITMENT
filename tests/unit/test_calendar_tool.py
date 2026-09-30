"""
Unit and Integration Tests for Milestone 4: Interview Scheduling Tool.

Validates:
1. Search: Valid slot search returns expected available slots.
2. Search: Candidate filtering restricts to specified candidate.
3. Search: Job filtering restricts to specified job.
4. Search: Date filtering restricts to specified date.
5. Search: Duration filtering restricts to specified duration.
6. Search: Timezone handling (Asia/Kolkata default and UTC conversion).
7. Search: No availability response returns structured no_slots status.
8. Search: Invalid input / schema validation handling.
9. Booking: Valid confirmed booking creates booking record and marks slot as booked.
10. Booking: Booking with confirmed=False returns confirmation_required.
11. Booking: Nonexistent slot returns invalid_slot.
12. Booking: Duplicate booking returns already_booked without overwrite.
13. Booking: Candidate mismatch returns candidate_mismatch.
14. Booking: Job mismatch returns job_mismatch.
15. Booking: State persistence during runtime (booked slot excluded from subsequent search).
16. Booking: Rejected bookings do not mutate calendar state.
17. Timezone: Models strictly require timezone-aware datetimes.
18. Agent: Agent invokes search tool for availability queries.
19. Agent: Agent handles no availability without inventing slots.
20. Agent: Agent requests confirmation before booking and executes on explicit confirmation.
"""

import json
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional

from pydantic import ValidationError
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.language_models.chat_models import BaseChatModel

from capabl_core.calendar.models import (
    CalendarEvent,
    InterviewSlot,
    InterviewBooking,
    SlotSearchResult,
    BookingResult,
)
from capabl_core.calendar.service import (
    MockCalendarService,
    create_initial_mock_slots,
    DEFAULT_CALENDAR_SERVICE,
)
from capabl_core.tools.calendar_tool import (
    SearchSlotsInput,
    BookInterviewInput,
    create_search_slots_tool,
    create_book_interview_tool,
    search_interview_slots,
    book_interview,
)
from capabl_core.agent.react_agent import (
    create_recruitment_agent,
    run_recruitment_agent,
    AgentExecutionResult,
)


class MockToolCallingChatModel(BaseChatModel):
    """Predictable mock chat model for unit testing agent tool calling."""
    messages_to_yield: List[AIMessage] = []
    current_index: int = 0

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.current_index < len(self.messages_to_yield):
            response_msg = self.messages_to_yield[self.current_index]
            self.current_index += 1
        else:
            response_msg = AIMessage(content="Default mock final answer.")
        return ChatResult(generations=[ChatGeneration(message=response_msg)])

    @property
    def _llm_type(self) -> str:
        return "mock-tool-calling-chat-model"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self


class TestInterviewSchedulingTool(unittest.TestCase):
    """Comprehensive test suite for Milestone 4 Interview Scheduling Tool."""

    def setUp(self):
        """Set up fresh isolated calendar service instance before each test."""
        self.service = MockCalendarService()
        self.search_tool = create_search_slots_tool(self.service)
        self.book_tool = create_book_interview_tool(self.service)
        DEFAULT_CALENDAR_SERVICE.reset()

    def test_01_valid_slot_search(self):
        """Search returns available slots for candidate and job."""
        res = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
        })
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["total_slots_found"], 0)
        self.assertTrue(all(s["candidate_id"] == "alex_chen" for s in res["slots"]))
        self.assertTrue(all(s["job_id"] == "jd_backend_lead_2026" for s in res["slots"]))
        self.assertTrue(all(s["status"] == "available" for s in res["slots"]))

    def test_02_candidate_filtering(self):
        """Search filters exclusively by candidate_id."""
        res_alex = self.search_tool.invoke({"candidate_id": "alex_chen"})
        res_priya = self.search_tool.invoke({"candidate_id": "priya_sharma"})

        self.assertEqual(res_alex["status"], "success")
        self.assertEqual(res_priya["status"], "success")
        self.assertTrue(all(s["candidate_id"] == "alex_chen" for s in res_alex["slots"]))
        self.assertTrue(all(s["candidate_id"] == "priya_sharma" for s in res_priya["slots"]))
        self.assertNotEqual(res_alex["total_slots_found"], res_priya["total_slots_found"])

    def test_03_job_filtering(self):
        """Search filters exclusively by job_id."""
        res_job = self.search_tool.invoke({"job_id": "jd_backend_lead_2026"})
        self.assertEqual(res_job["status"], "success")
        self.assertTrue(all(s["job_id"] == "jd_backend_lead_2026" for s in res_job["slots"]))

        # Nonexistent job should yield no slots
        res_empty = self.search_tool.invoke({"job_id": "jd_nonexistent_2026"})
        self.assertEqual(res_empty["status"], "no_slots")
        self.assertEqual(res_empty["total_slots_found"], 0)

    def test_04_date_filtering(self):
        """Search accurately filters slots by exact date and date range."""
        # Exact date
        res_date = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "date": "2026-09-29",
        })
        self.assertEqual(res_date["status"], "success")
        for slot in res_date["slots"]:
            self.assertTrue(slot["start_time"].startswith("2026-09-29"))

        # Date range
        res_range = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "start_date": "2026-09-30",
            "end_date": "2026-09-30",
        })
        self.assertEqual(res_range["status"], "success")
        for slot in res_range["slots"]:
            self.assertTrue(slot["start_time"].startswith("2026-09-30"))

    def test_05_duration_filtering(self):
        """Search accurately filters by slot duration in minutes."""
        res_30 = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "duration_minutes": 30,
        })
        self.assertEqual(res_30["status"], "success")
        self.assertTrue(all(s["duration_minutes"] == 30 for s in res_30["slots"]))

        res_60 = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "duration_minutes": 60,
        })
        self.assertEqual(res_60["status"], "success")
        self.assertEqual(res_60["total_slots_found"], 1)
        self.assertEqual(res_60["slots"][0]["slot_id"], "slot_003")

    def test_06_timezone_handling(self):
        """Search supports timezone conversion while preserving time accuracy."""
        # Default Asia/Kolkata
        res_kolkata = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "date": "2026-09-29",
            "timezone": "Asia/Kolkata",
        })
        self.assertEqual(res_kolkata["timezone"], "Asia/Kolkata")
        slot_k = res_kolkata["slots"][0]
        self.assertIn("Asia/Kolkata", slot_k["display_time"])

        # Query in UTC: 10:00 AM IST on 2026-09-29 is 04:30 AM UTC
        res_utc = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "date": "2026-09-29",
            "timezone": "UTC",
        })
        self.assertEqual(res_utc["status"], "success")
        self.assertEqual(res_utc["timezone"], "UTC")
        slot_u = res_utc["slots"][0]
        self.assertIn("04:30 AM", slot_u["display_time"])
        self.assertIn("UTC", slot_u["display_time"])

    def test_07_no_availability_response(self):
        """Search returns structured no_slots result when criteria yields no matches."""
        res = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "date": "2026-12-31",
        })
        self.assertEqual(res["status"], "no_slots")
        self.assertEqual(res["total_slots_found"], 0)
        self.assertEqual(res["slots"], [])
        self.assertIn("No available interview slots", res["message"])

    def test_08_invalid_input_handling(self):
        """Tool gracefully handles unknown timezones by falling back to Asia/Kolkata."""
        res = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "timezone": "Invalid/Unknown_TZ",
        })
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["timezone"], "Asia/Kolkata")

    def test_09_valid_confirmed_booking(self):
        """Explicitly confirmed booking succeeds and marks slot booked."""
        res = self.book_tool.invoke({
            "slot_id": "slot_001",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "confirmed": True,
            "notes": "Recruiter approved slot",
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("Interview successfully confirmed and booked", res["message"])
        self.assertIsNotNone(res["booking"])
        self.assertEqual(res["booking"]["slot_id"], "slot_001")
        self.assertEqual(res["booking"]["candidate_id"], "alex_chen")
        self.assertEqual(res["booking"]["status"], "confirmed")

        # Verify underlying service state
        slot = self.service.get_slot("slot_001")
        self.assertEqual(slot.status, "booked")
        booking = self.service.get_booking("slot_001")
        self.assertIsNotNone(booking)
        self.assertEqual(booking.slot_id, "slot_001")

    def test_10_confirmation_required(self):
        """Booking with confirmed=False is rejected without state mutation."""
        res = self.book_tool.invoke({
            "slot_id": "slot_001",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "confirmed": False,
        })
        self.assertEqual(res["status"], "confirmation_required")
        self.assertIn("Explicit user confirmation is required", res["message"])
        self.assertIsNone(res["booking"])

        # Slot must remain available
        slot = self.service.get_slot("slot_001")
        self.assertEqual(slot.status, "available")
        self.assertIsNone(self.service.get_booking("slot_001"))

    def test_11_nonexistent_slot(self):
        """Booking a nonexistent slot returns invalid_slot."""
        res = self.book_tool.invoke({
            "slot_id": "slot_9999",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "confirmed": True,
        })
        self.assertEqual(res["status"], "invalid_slot")
        self.assertIn("does not exist", res["message"])
        self.assertIsNone(res["booking"])

    def test_12_duplicate_booking(self):
        """Attempting to book an already booked slot returns already_booked."""
        # First booking succeeds
        res1 = self.book_tool.invoke({
            "slot_id": "slot_001",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "confirmed": True,
        })
        self.assertEqual(res1["status"], "success")

        # Second booking attempt on same slot fails
        res2 = self.book_tool.invoke({
            "slot_id": "slot_001",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "confirmed": True,
        })
        self.assertEqual(res2["status"], "already_booked")
        self.assertIn("already booked and cannot be double-booked", res2["message"])
        self.assertIsNone(res2["booking"])

    def test_13_candidate_mismatch(self):
        """Booking with candidate mismatch returns candidate_mismatch."""
        res = self.book_tool.invoke({
            "slot_id": "slot_001",  # belongs to alex_chen
            "candidate_id": "priya_sharma",
            "job_id": "jd_backend_lead_2026",
            "confirmed": True,
        })
        self.assertEqual(res["status"], "candidate_mismatch")
        self.assertIn("is configured for candidate 'alex_chen'", res["message"])
        self.assertIsNone(res["booking"])
        # Slot must remain available
        self.assertEqual(self.service.get_slot("slot_001").status, "available")

    def test_14_job_mismatch(self):
        """Booking with job mismatch returns job_mismatch."""
        res = self.book_tool.invoke({
            "slot_id": "slot_001",  # belongs to jd_backend_lead_2026
            "candidate_id": "alex_chen",
            "job_id": "jd_frontend_lead_2026",
            "confirmed": True,
        })
        self.assertEqual(res["status"], "job_mismatch")
        self.assertIn("is configured for job 'jd_backend_lead_2026'", res["message"])
        self.assertIsNone(res["booking"])
        # Slot must remain available
        self.assertEqual(self.service.get_slot("slot_001").status, "available")

    def test_15_booking_state_persistence_in_runtime(self):
        """After booking a slot, subsequent searches in runtime exclude that slot."""
        # Check slot_001 is initially present
        search1 = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "date": "2026-09-29",
        })
        slot_ids1 = [s["slot_id"] for s in search1["slots"]]
        self.assertIn("slot_001", slot_ids1)

        # Book slot_001
        self.book_tool.invoke({
            "slot_id": "slot_001",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "confirmed": True,
        })

        # Search again: slot_001 must not be in available slots
        search2 = self.search_tool.invoke({
            "candidate_id": "alex_chen",
            "date": "2026-09-29",
        })
        slot_ids2 = [s["slot_id"] for s in search2["slots"]]
        self.assertNotIn("slot_001", slot_ids2)
        self.assertEqual(len(slot_ids2), len(slot_ids1) - 1)

    def test_16_rejected_booking_does_not_mutate_state(self):
        """Failed booking attempts leave slot available and do not create bookings."""
        # Attempt booking without confirmation
        self.book_tool.invoke({
            "slot_id": "slot_002",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "confirmed": False,
        })
        self.assertEqual(self.service.get_slot("slot_002").status, "available")
        self.assertIsNone(self.service.get_booking("slot_002"))

        # Attempt booking with mismatch
        self.book_tool.invoke({
            "slot_id": "slot_002",
            "candidate_id": "wrong_person",
            "job_id": "jd_backend_lead_2026",
            "confirmed": True,
        })
        self.assertEqual(self.service.get_slot("slot_002").status, "available")
        self.assertIsNone(self.service.get_booking("slot_002"))

    def test_17_timezone_aware_models_enforcement(self):
        """Pydantic calendar models strictly reject naive datetimes."""
        kolkata = ZoneInfo("Asia/Kolkata")
        naive_dt = datetime(2026, 9, 29, 10, 0)
        aware_dt = datetime(2026, 9, 29, 10, 0, tzinfo=kolkata)

        # Naive datetime must raise ValidationError
        with self.assertRaises(ValidationError):
            InterviewSlot(
                slot_id="test_slot",
                candidate_id="alex_chen",
                job_id="jd_test",
                start_time=naive_dt,
                end_time=aware_dt,
            )

        with self.assertRaises(ValidationError):
            InterviewBooking(
                booking_id="b_test",
                slot_id="s_test",
                candidate_id="alex_chen",
                job_id="jd_test",
                start_time=naive_dt,
                end_time=aware_dt,
                created_at=aware_dt,
            )

        with self.assertRaises(ValidationError):
            CalendarEvent(
                event_id="e_test",
                title="Test Event",
                start_time=naive_dt,
                end_time=aware_dt,
            )

    def test_18_agent_invokes_search_tool_for_availability(self):
        """Agent invokes search_interview_slots when asked about availability."""
        # Configure mock model to call search_interview_slots then answer
        mock_llm = MockToolCallingChatModel()
        mock_llm.messages_to_yield = [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "search_interview_slots",
                    "args": {"candidate_id": "alex_chen", "date": "2026-09-29"},
                    "id": "call_search_1",
                }],
            ),
            AIMessage(
                content="Alex Chen has 3 available interview slots on Tuesday, 29 September 2026."
            ),
        ]

        agent = create_recruitment_agent(
            llm=mock_llm,
            tools=[self.search_tool, self.book_tool],
        )

        result: AgentExecutionResult = run_recruitment_agent(
            agent=agent,
            query="Find available interview slots for Alex Chen on 2026-09-29.",
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0]["tool_name"], "search_interview_slots")
        self.assertEqual(result.tool_calls[0]["arguments"]["candidate_id"], "alex_chen")
        self.assertIn("Alex Chen has 3 available", result.answer)
        self.assertTrue(any(s["document_type"] == "calendar_slot" for s in result.sources))

    def test_19_agent_handles_no_availability_without_invention(self):
        """Agent reports no available slots when search yields no slots."""
        mock_llm = MockToolCallingChatModel()
        mock_llm.messages_to_yield = [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "search_interview_slots",
                    "args": {"candidate_id": "alex_chen", "date": "2026-12-31"},
                    "id": "call_search_none",
                }],
            ),
            AIMessage(
                content="There are no available interview slots for Alex Chen on 2026-12-31."
            ),
        ]

        agent = create_recruitment_agent(
            llm=mock_llm,
            tools=[self.search_tool, self.book_tool],
        )

        result: AgentExecutionResult = run_recruitment_agent(
            agent=agent,
            query="Are there any interview slots for Alex Chen on 2026-12-31?",
        )

        self.assertEqual(result.status, "no_evidence")
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0]["tool_name"], "search_interview_slots")
        self.assertIn("no available interview slots", result.answer)

    def test_20_agent_requests_confirmation_and_executes_when_confirmed(self):
        """
        Agent flow:
        1. When user requests booking, agent first presents proposed slot and seeks confirmation.
        2. When user confirms, agent calls book_interview with confirmed=True.
        """
        # Step 1: User says "Book slot_001 for Alex Chen" -> Agent proposes and asks for confirmation
        mock_llm_step1 = MockToolCallingChatModel()
        mock_llm_step1.messages_to_yield = [
            AIMessage(
                content=(
                    "I found slot_001 for Alex Chen (Senior Backend Lead) on Tuesday, "
                    "29 September 2026 from 10:00 AM to 10:30 AM Asia/Kolkata with Vikram Malhotra. "
                    "Please confirm: Would you like me to book this interview slot?"
                )
            )
        ]

        agent1 = create_recruitment_agent(
            llm=mock_llm_step1,
            tools=[self.search_tool, self.book_tool],
        )

        result1: AgentExecutionResult = run_recruitment_agent(
            agent=agent1,
            query="Book slot_001 for Alex Chen.",
        )
        self.assertEqual(result1.status, "success")
        self.assertEqual(len(result1.tool_calls), 0)  # No premature tool call without confirmation
        self.assertIn("Please confirm", result1.answer)
        self.assertEqual(self.service.get_slot("slot_001").status, "available")

        # Step 2: User confirms -> Agent calls book_interview(confirmed=True)
        mock_llm_step2 = MockToolCallingChatModel()
        mock_llm_step2.messages_to_yield = [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "book_interview",
                    "args": {
                        "slot_id": "slot_001",
                        "candidate_id": "alex_chen",
                        "job_id": "jd_backend_lead_2026",
                        "confirmed": True,
                    },
                    "id": "call_book_confirmed",
                }],
            ),
            AIMessage(
                content="Interview has been successfully confirmed and booked for Alex Chen on Tuesday, 29 September 2026."
            ),
        ]

        agent2 = create_recruitment_agent(
            llm=mock_llm_step2,
            tools=[self.search_tool, self.book_tool],
        )

        result2: AgentExecutionResult = run_recruitment_agent(
            agent=agent2,
            query="Yes, I confirm. Please proceed with booking slot_001 for Alex Chen.",
        )

        self.assertEqual(result2.status, "success")
        self.assertEqual(len(result2.tool_calls), 1)
        self.assertEqual(result2.tool_calls[0]["tool_name"], "book_interview")
        self.assertTrue(result2.tool_calls[0]["arguments"]["confirmed"])
        self.assertIn("Interview has been successfully confirmed and booked", result2.answer)
        self.assertEqual(self.service.get_slot("slot_001").status, "booked")
        self.assertIsNotNone(self.service.get_booking("slot_001"))


if __name__ == "__main__":
    unittest.main()
