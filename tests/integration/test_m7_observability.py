"""
Integration tests for Milestone 7 Observability & Compliance Audit Logger.

Tests:
1. RecruitmentAuditLogger initializes and creates log directory/file.
2. Structured logging appends valid JSONL records.
3. Correlation session_id is persisted across events.
4. Sensitive secrets (api_key, password, token) are redacted.
5. Large document payloads are truncated/summarized.
6. Helper methods emit correct event categories.
7. Querying recent events filters properly by session and event type.
8. Logger fails safely without throwing exceptions if file writing fails.
"""

import json
import pytest
from pathlib import Path
from enhancement.security.audit_logger import (
    RecruitmentAuditLogger,
    sanitize_payload,
)


class TestRecruitmentAuditLogger:

    @pytest.fixture
    def test_logger(self, tmp_path: Path):
        log_dir = tmp_path / "test_audit"
        return RecruitmentAuditLogger(log_directory=log_dir)

    def test_01_initialization_and_directory_creation(self, test_logger: RecruitmentAuditLogger):
        assert test_logger.log_directory.exists()
        assert not test_logger.log_file.exists() or test_logger.log_file.stat().st_size == 0

    def test_02_log_event_appends_valid_jsonl(self, test_logger: RecruitmentAuditLogger):
        record = test_logger.log_event(
            event="test_event",
            session_id="sess_001",
            status="success",
            duration_ms=45.2,
            payload={"key": "value"},
        )
        assert record["event"] == "test_event"
        assert record["session_id"] == "sess_001"
        assert record["status"] == "success"
        assert record["duration_ms"] == 45.2
        assert record["payload"] == {"key": "value"}

        assert test_logger.log_file.exists()
        with open(test_logger.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 1
        loaded = json.loads(lines[0])
        assert loaded["event_id"] == record["event_id"]
        assert loaded["event"] == "test_event"

    def test_03_secrets_redaction(self):
        dirty_payload = {
            "api_key": "sk-1234567890abcdef",
            "groq_api_key": "gsk_secret_token",
            "password": "supersecretpassword",
            "token": "bearer-xyz",
            "nested": {
                "secret_key": "nested_secret",
                "normal_field": "safe_data",
            },
        }
        cleaned = sanitize_payload(dirty_payload)
        assert cleaned["api_key"] == "[REDACTED_SECRET]"
        assert cleaned["groq_api_key"] == "[REDACTED_SECRET]"
        assert cleaned["password"] == "[REDACTED_SECRET]"
        assert cleaned["token"] == "[REDACTED_SECRET]"
        assert cleaned["nested"]["secret_key"] == "[REDACTED_SECRET]"
        assert cleaned["nested"]["normal_field"] == "safe_data"

    def test_04_large_document_payload_summarized(self):
        long_text = "Experienced software engineer with distributed systems " * 50
        payload = {
            "page_content": long_text,
            "raw_text": long_text,
            "candidate_name": "Alex Chen",
        }
        cleaned = sanitize_payload(payload)
        assert cleaned["candidate_name"] == "Alex Chen"
        assert "[PREVIEW:" in cleaned["page_content"]
        assert "[PREVIEW:" in cleaned["raw_text"]

    def test_05_convenience_event_helpers(self, test_logger: RecruitmentAuditLogger):
        test_logger.log_session_start(session_id="sess_alpha")
        test_logger.log_document_ingested(
            document_id="alex_chen",
            document_type="resume",
            chunk_count=5,
            session_id="sess_alpha",
            candidate_id="alex_chen",
        )
        test_logger.log_retrieval_started(query="Python skills", document_type="resume", session_id="sess_alpha")
        test_logger.log_retrieval_completed(
            query="Python skills",
            document_type="resume",
            retrieved_count=3,
            duration_ms=12.4,
            session_id="sess_alpha",
        )
        test_logger.log_match_started(candidate_id="alex_chen", job_id="jd_001", session_id="sess_alpha")
        test_logger.log_match_completed(
            candidate_id="alex_chen",
            job_id="jd_001",
            matched_skills=["python", "fastapi"],
            missing_skills=["rest"],
            duration_ms=8.5,
            session_id="sess_alpha",
        )
        test_logger.log_tool_blocked(tool_name="book_interview", reason="confirmation_required", session_id="sess_alpha")
        test_logger.log_booking_confirmed(booking_id="b_1", slot_id="s_1", candidate_id="alex_chen", session_id="sess_alpha")
        test_logger.log_security_event(event_sub_type="injection_detected", message="Hostile instruction ignored", session_id="sess_alpha")

        events = test_logger.get_recent_events(limit=20, session_id="sess_alpha")
        assert len(events) == 9
        event_names = [e["event"] for e in events]
        assert "session_started" in event_names
        assert "document_ingested" in event_names
        assert "match_completed" in event_names
        assert "tool_blocked" in event_names
        assert "booking_confirmed" in event_names
        assert "security_event" in event_names

    def test_06_filtering_and_querying_events(self, test_logger: RecruitmentAuditLogger):
        test_logger.log_event("event_a", session_id="sess_1")
        test_logger.log_event("event_b", session_id="sess_2")
        test_logger.log_event("event_a", session_id="sess_2")

        sess_1_events = test_logger.get_recent_events(session_id="sess_1")
        assert len(sess_1_events) == 1
        assert sess_1_events[0]["session_id"] == "sess_1"

        type_a_events = test_logger.get_recent_events(event_type="event_a")
        assert len(type_a_events) == 2

    def test_07_safe_error_handling(self, test_logger: RecruitmentAuditLogger):
        # Even with an un-writable directory, log_event should not raise
        bad_logger = RecruitmentAuditLogger(log_directory=Path("/non_existent_drive_root/impossible/path"))
        record = bad_logger.log_event("test_fail", session_id="fail_sess")
        assert record["event"] == "test_fail"
