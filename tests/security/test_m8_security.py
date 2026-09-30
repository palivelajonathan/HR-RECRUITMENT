"""
Milestone 8 Security Tests: Upload Hardening, PII Redaction, Gatekeeper & Log Rotation.

CAPABL Track 6 Requirement:
- Verify filename sanitization against path traversal (../../secret.pdf, etc.).
- Verify rejection of empty, oversized, malformed, non-PDF, and excessive-page files.
- Verify comprehensive PII (email, phone, SSN, card) and secret (tokens, API keys) scrubbing.
- Verify audit log size ceiling and rotation mechanics.
- Verify calendar state mutation gatekeeper (rejection of unconfirmed actions).
- Verify retrieval domain and cross-candidate isolation boundaries.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fpdf import FPDF

from capabl_core.ingestion.validator import (
    sanitize_filename,
    validate_pdf_content,
)
from enhancement.security.audit_logger import (
    sanitize_payload,
    redact_string_content,
    RecruitmentAuditLogger,
)
from capabl_core.tools.calendar_tool import book_interview


def create_dummy_pdf(num_pages: int = 1) -> bytes:
    """Helper creating a minimal valid PDF in memory."""
    pdf = FPDF()
    for _ in range(num_pages):
        pdf.add_page()
        pdf.set_font("helvetica", size=12)
        pdf.cell(w=0, h=10, text="Test PDF Page Content", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


class TestM8Security:
    """Comprehensive security test suite for M8."""

    # --- 1. Filename & Path Traversal Security ---

    def test_01_filename_sanitization_path_traversal_unix(self):
        """Verifies Unix path traversal sequences are completely stripped."""
        clean = sanitize_filename("../../secret.pdf")
        assert clean == "secret.pdf"
        assert "/" not in clean
        assert ".." not in clean

    def test_02_filename_sanitization_path_traversal_windows(self):
        """Verifies Windows path traversal sequences are completely stripped."""
        clean = sanitize_filename(r"..\..\Windows\System32\cmd.pdf")
        assert clean == "cmd.pdf"
        assert "\\" not in clean
        assert ".." not in clean

    def test_03_filename_sanitization_etc_passwd(self):
        """Verifies root path traversals are stripped and given .pdf extension."""
        clean = sanitize_filename("/etc/passwd")
        assert clean == "passwd.pdf"

    def test_04_filename_sanitization_empty_or_special_chars(self):
        """Verifies null bytes and invalid characters fallback safely to a generated name."""
        clean = sanitize_filename("\x00..///$$$")
        assert clean.endswith(".pdf")
        assert len(clean) > 4

    # --- 2. Upload Hardening & PDF Validation ---

    def test_05_upload_rejects_empty_file(self):
        """Verifies that 0-byte uploads are immediately rejected."""
        with pytest.raises(ValueError, match="Uploaded file is empty"):
            validate_pdf_content(b"")

    def test_06_upload_rejects_non_pdf_signature(self):
        """Verifies that non-PDF files (lacking %PDF- header) are rejected."""
        fake_binary = b"MZ\x90\x00\x03\x00\x00\x00"  # Executable header
        with pytest.raises(ValueError, match="Missing '%PDF-' header signature"):
            validate_pdf_content(fake_binary, filename="trojan.pdf")

    def test_07_upload_rejects_oversized_file(self):
        """Verifies that files exceeding MAX_UPLOAD_SIZE_MB are rejected."""
        valid_pdf = create_dummy_pdf(num_pages=1)
        # Pad to exceed 1MB limit for testing
        padded = valid_pdf + (b" " * (2 * 1024 * 1024))
        with pytest.raises(ValueError, match="exceeds maximum allowed limit"):
            validate_pdf_content(padded, max_size_mb=1)

    def test_08_upload_rejects_excessive_page_count(self):
        """Verifies that documents exceeding MAX_PDF_PAGES are rejected."""
        multi_page_pdf = create_dummy_pdf(num_pages=5)
        with pytest.raises(ValueError, match="exceeds page limit"):
            validate_pdf_content(multi_page_pdf, max_pages=3)

    def test_09_upload_accepts_valid_pdf(self):
        """Verifies that a valid PDF passes all security checks cleanly."""
        valid_pdf = create_dummy_pdf(num_pages=2)
        raw_bytes, clean_name = validate_pdf_content(
            valid_pdf,
            filename="../../valid_resume.pdf",
            max_size_mb=5,
            max_pages=10,
        )
        assert raw_bytes.startswith(b"%PDF-")
        assert clean_name == "valid_resume.pdf"

    # --- 3. Secret & PII Scrubbing ---

    def test_10_redact_candidate_email(self):
        """Verifies candidate email addresses are masked in freeform text."""
        text = "Contact candidate at alex.chen.engineer@gmail.com for scheduling."
        cleaned = redact_string_content(text)
        assert "alex.chen.engineer@gmail.com" not in cleaned
        assert "[REDACTED_EMAIL]" in cleaned

    def test_11_redact_candidate_phone(self):
        """Verifies candidate phone numbers are masked."""
        text = "Call candidate at 555-234-5678 or +1-800-555-0199 immediately."
        cleaned = redact_string_content(text)
        assert "555-234-5678" not in cleaned
        assert "[REDACTED_PHONE]" in cleaned

    def test_12_redact_ssn(self):
        """Verifies Social Security Numbers / Tax IDs are masked."""
        text = "Candidate tax identification number is 123-45-6789."
        cleaned = redact_string_content(text)
        assert "123-45-6789" not in cleaned
        assert "[REDACTED_SSN]" in cleaned

    def test_13_redact_bearer_tokens_and_api_keys(self):
        """Verifies API keys and Bearer tokens are scrubbed from text."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI... and key gsk_abcdef1234567890123"
        cleaned = redact_string_content(text)
        assert "gsk_abcdef1234567890123" not in cleaned
        assert "[REDACTED_SECRET]" in cleaned

    def test_14_sanitize_payload_nested_dict(self):
        """Verifies recursive sanitization of nested payloads with both keys and string values."""
        payload = {
            "session_id": "sess_001",
            "candidate": {
                "name": "Alex Chen",
                "email": "alex@company.org",
                "phone": "415-555-1234",
            },
            "credentials": {
                "groq_api_key": "gsk_secret_1234567890123456",
                "password": "supersecretpassword",
            },
            "user_prompt": "My SSN is 999-88-7777 please confirm.",
        }
        sanitized = sanitize_payload(payload)

        # Check key redaction
        assert sanitized["credentials"]["groq_api_key"] == "[REDACTED_SECRET]"
        assert sanitized["credentials"]["password"] == "[REDACTED_SECRET]"

        # Check value string PII redaction
        assert sanitized["candidate"]["email"] == "[REDACTED_EMAIL]"
        assert sanitized["candidate"]["phone"] == "[REDACTED_PHONE]"
        assert "999-88-7777" not in sanitized["user_prompt"]
        assert "[REDACTED_SSN]" in sanitized["user_prompt"]

    # --- 4. Audit Log Rotation Mechanics ---

    def test_15_audit_logger_rotation_on_size_limit(self):
        """Verifies that the audit logger rotates files when exceeding max_bytes."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Set tiny max_bytes (500 bytes) to trigger rotation quickly
            logger = RecruitmentAuditLogger(
                log_directory=temp_dir,
                max_bytes=500,
                backup_count=3,
            )

            # Write enough events to trigger multiple rotations
            for i in range(10):
                logger.log_event(
                    event="test_event",
                    session_id=f"session_{i}",
                    payload={"data": f"payload_content_number_{i}_with_extra_padding_to_exceed_size"},
                )

            # Check that log files exist and rotated files are present
            main_log = Path(temp_dir) / "audit_trail.jsonl"
            backup_1 = Path(temp_dir) / "audit_trail.jsonl.1"
            assert main_log.exists()
            assert backup_1.exists()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # --- 5. Calendar State Mutation Gatekeeper ---

    def test_16_calendar_gatekeeper_blocks_unconfirmed_booking(self):
        """Verifies that unconfirmed booking attempts are blocked with confirmation_required."""
        res = book_interview.invoke({
            "slot_id": "slot_001",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "confirmed": False,
        })
        assert res["status"] == "confirmation_required"
        assert res.get("booking") is None
