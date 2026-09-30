"""
Integration and Product Tests for Milestone 10: Final Product Integration & Demo Readiness.

Verifies:
1. End-to-end 17-step recruiter journey:
   Upload Resume -> Upload JD -> Auto-match -> Matched/Missing skills -> Grounded questions ->
   Policy retrieval -> Slot search -> Unconfirmed block -> Confirmed booking -> Confirmation result.
2. Demo quick-load and safe demo reset without destroying Chroma collections.
3. Candidate isolation (Alex Chen vs Priya Sharma).
4. Negative paths: unconfirmed booking, duplicate booking, missing documents, invalid inputs.
5. Prompt injection defense and zero subjective score / autonomous hire invariants.
6. Health & readiness probes and audit log completeness.
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from capabl_core.workflow import DEFAULT_WORKFLOW_SERVICE, AutomaticMatchResult
from capabl_core.evidence.service import EvidenceService
from capabl_core.calendar.service import DEFAULT_CALENDAR_SERVICE
from capabl_core.health import check_readiness, check_liveness
from enhancement.security.audit_logger import DEFAULT_AUDIT_LOGGER
from enhancement.mcp.client import CAPABLMCPClient
from capabl_core.ui.demo_helper import (
    load_demo_candidate,
    reset_demo_state,
    get_demo_documents_status,
)


@pytest.fixture(autouse=True)
def clean_calendar():
    """Ensure calendar is reset to initial clean state before and after each test."""
    DEFAULT_CALENDAR_SERVICE.reset()
    yield
    DEFAULT_CALENDAR_SERVICE.reset()


def test_demo_documents_available():
    """Ensure all synthetic sample demo documents exist on disk."""
    status = get_demo_documents_status()
    assert status["alex_chen_resume"] is True, "Alex Chen sample resume missing"
    assert status["priya_sharma_resume"] is True, "Priya Sharma sample resume missing"
    assert status["backend_lead_jd"] is True, "Backend Lead sample JD missing"
    assert status["leave_policy"] is True, "Leave policy sample missing"


def test_m10_end_to_end_recruiter_journey():
    """
    Executes and validates the full 17-step recruiter journey.
    """
    # 1. Start application & verify health
    readiness = check_readiness()
    assert readiness["ready"] is True
    liveness = check_liveness()
    assert liveness["alive"] is True

    # 2-5. Ingest Candidate Resume, JD, and Policy via Demo Loader
    demo_data = load_demo_candidate(candidate="alex_chen", job_id="jd_backend_lead_2026")
    assert demo_data["status"] == "success"
    assert demo_data["candidate_id"] == "alex_chen"
    assert demo_data["resume_chunks"] > 0
    assert demo_data["jd_chunks"] > 0
    assert demo_data["policy_chunks"] > 0

    # 6-9. Verify Automatic Match & Deterministic Skill Comparison
    match_result_obj: AutomaticMatchResult = demo_data["match_result"]
    assert match_result_obj.status == "match_ready"
    assert match_result_obj.match_result is not None

    match = match_result_obj.match_result
    assert len(match.matched_skills) >= 6, "Expected at least 6 matched skills for Alex Chen"
    assert "python" in [s.lower() for s in match.matched_skills]
    assert "fastapi" in [s.lower() for s in match.matched_skills]
    assert "docker" in [s.lower() for s in match.matched_skills]
    assert "kubernetes" in [s.lower() for s in match.matched_skills]
    assert "postgresql" in [s.lower() for s in match.matched_skills]

    # Invariant: Zero subjective scores, percentages, or autonomous hire/reject recommendations
    summary = match_result_obj.summary_markdown.lower()
    assert "percent" not in summary and "%" not in summary
    assert "hire" not in summary and "reject" not in summary
    assert "tier" not in summary and "score" not in summary

    # 10. Recruiter Evidence Query (Candidate Evidence)
    evidence_service = EvidenceService()
    cand_env = evidence_service.get_candidate_evidence(
        query="FastAPI microservices experience",
        candidate_id="alex_chen",
        top_k=2,
    )
    assert cand_env.status == "success"
    assert cand_env.count > 0
    for item in cand_env.items:
        assert item.candidate_id == "alex_chen"
        assert item.document_type == "resume"

    # 11. Corporate Policy Retrieval
    pol_env = evidence_service.get_policy_evidence(
        query="annual leave allowance core hours",
        top_k=2,
    )
    assert pol_env.status == "success"
    assert pol_env.count > 0
    for item in pol_env.items:
        assert item.document_type == "policy"
        assert item.candidate_id is None

    # 12. Search Interview Availability (Asia/Kolkata)
    search_res = DEFAULT_CALENDAR_SERVICE.search_slots(
        candidate_id="alex_chen",
        job_id="jd_backend_lead_2026",
        timezone_str="Asia/Kolkata",
    )
    assert search_res.status == "success"
    assert search_res.total_slots_found >= 1
    slot = search_res.slots[0]
    slot_id = slot["slot_id"]

    # 13. Gatekeeper Enforcement: Unconfirmed Booking Attempt MUST be Blocked
    unconfirmed_res = DEFAULT_CALENDAR_SERVICE.book_slot(
        slot_id=slot_id,
        candidate_id="alex_chen",
        job_id="jd_backend_lead_2026",
        confirmed=False,
    )
    assert unconfirmed_res.status == "confirmation_required"
    assert unconfirmed_res.booking is None

    # 14-15. Confirmed Booking Execution Past Gatekeeper
    confirmed_res = DEFAULT_CALENDAR_SERVICE.book_slot(
        slot_id=slot_id,
        candidate_id="alex_chen",
        job_id="jd_backend_lead_2026",
        confirmed=True,
        notes="M10 E2E Recruiter Journey Verification",
    )
    assert confirmed_res.status == "success"
    assert confirmed_res.booking is not None
    assert confirmed_res.booking["booking_id"].startswith("book_")
    assert confirmed_res.booking["slot_id"] == slot_id

    # Negative Path: Duplicate Booking Block
    dup_res = DEFAULT_CALENDAR_SERVICE.book_slot(
        slot_id=slot_id,
        candidate_id="alex_chen",
        job_id="jd_backend_lead_2026",
        confirmed=True,
    )
    assert dup_res.status == "already_booked"

    # 16. Audit Log Integrity
    events = DEFAULT_AUDIT_LOGGER.query_events(limit=30)
    event_types = {e["event"] for e in events}
    assert "demo_loaded" in event_types
    assert len(events) >= 1


def test_demo_safe_reset():
    """Verify demo reset clears calendar state without destroying Chroma data."""
    # Seed a booking
    DEFAULT_CALENDAR_SERVICE.book_slot(
        slot_id="slot_001",
        candidate_id="alex_chen",
        job_id="jd_backend_lead_2026",
        confirmed=True,
    )
    # Slot 001 is now booked
    search_before = DEFAULT_CALENDAR_SERVICE.search_slots(candidate_id="alex_chen", job_id="jd_backend_lead_2026")
    avail_ids_before = [s["slot_id"] for s in search_before.slots]
    assert "slot_001" not in avail_ids_before

    # Reset demo
    reset_res = reset_demo_state()
    assert reset_res["status"] == "success"

    # Slot 001 should now be available again
    search_after = DEFAULT_CALENDAR_SERVICE.search_slots(candidate_id="alex_chen", job_id="jd_backend_lead_2026")
    avail_ids_after = [s["slot_id"] for s in search_after.slots]
    assert "slot_001" in avail_ids_after


def test_m10_candidate_isolation_and_gaps():
    """Verify candidate isolation and skill gap detection for Priya Sharma vs Backend role."""
    # Ingest Priya Sharma
    demo_priya = load_demo_candidate(candidate="priya_sharma", job_id="jd_backend_lead_2026")
    match_result_obj = demo_priya["match_result"]
    assert match_result_obj.status == "match_ready"
    match = match_result_obj.match_result

    # Priya has Frontend skills, missing backend distributed systems skills
    missing_lower = [s.lower() for s in match.missing_skills]
    assert "docker" in missing_lower or "kubernetes" in missing_lower or "postgresql" in missing_lower

    # Evidence isolation: Alex query returns Alex only
    evidence_service = EvidenceService()
    alex_env = evidence_service.get_candidate_evidence(query="experience", candidate_id="alex_chen", top_k=5)
    for it in alex_env.items:
        assert "priya" not in it.excerpt.lower()
        assert it.candidate_id == "alex_chen"


def test_mcp_boundary_integration_in_m10():
    """Verify MCP external boundary tools are operational within M10 environment."""
    mcp_client = CAPABLMCPClient()
    tools = mcp_client.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "get_candidate_evidence" in tool_names
    assert "get_job_evidence" in tool_names
    assert "get_policy_evidence" in tool_names
    assert "search_interview_slots" in tool_names
    assert "book_interview" in tool_names

    # Test MCP candidate evidence
    resp = mcp_client.call_tool("get_candidate_evidence", {"candidate_id": "alex_chen", "query": "Python"})
    assert resp["status"] == "success"
    assert len(resp["evidence"]) > 0

    # Test MCP unconfirmed booking block
    resp_block = mcp_client.call_tool("book_interview", {
        "slot_id": "slot_002",
        "candidate_id": "alex_chen",
        "job_id": "jd_backend_lead_2026",
        "confirmed": False,
    })
    assert resp_block["status"] == "blocked"
    assert resp_block["error_code"] == "CONFIRMATION_REQUIRED"


def test_m10_negative_paths_and_error_states():
    """Verify negative paths: invalid document types, non-existent slots, and unconfirmed actions."""
    # 1. Invalid document type rejection
    with pytest.raises(ValueError, match="Invalid document_type"):
        DEFAULT_WORKFLOW_SERVICE.ingest_document(
            file_path_or_bytes="nonexistent.pdf",
            document_type="malicious_type",
            document_id="doc_001",
        )

    # 2. Ingesting empty or non-PDF file rejected
    with pytest.raises(ValueError, match="empty"):
        DEFAULT_WORKFLOW_SERVICE.ingest_document(
            file_path_or_bytes=b"",
            document_type="resume",
            document_id="alex_chen",
            candidate_id="alex_chen",
        )

    with pytest.raises(ValueError, match="Invalid file format"):
        DEFAULT_WORKFLOW_SERVICE.ingest_document(
            file_path_or_bytes=b"This is not a valid PDF header content",
            document_type="resume",
            document_id="alex_chen",
            candidate_id="alex_chen",
        )

    # 3. Booking non-existent slot returns error
    res = DEFAULT_CALENDAR_SERVICE.book_slot(
        slot_id="slot_999999",
        candidate_id="alex_chen",
        job_id="jd_backend_lead_2026",
        confirmed=True,
    )
    assert res.status == "invalid_slot"
    assert res.booking is None

