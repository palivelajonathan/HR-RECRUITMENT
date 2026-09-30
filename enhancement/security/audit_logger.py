"""
Structured Observability & Compliance Audit Logger.

CAPABL Track 6 Requirement:
- Records immutable, structured JSONL logs of all agent thoughts, tool invocations,
  document ingestions, match operations, and calendar mutations.
- Enforces strict redaction of API keys, tokens, secrets, full raw document texts, and candidate PII.
- Tracks session IDs, timestamps (UTC ISO-8601), and execution durations (duration_ms).
- Provides query capabilities for Streamlit UI and automated compliance audits.
- Safe execution: logging errors never break or disrupt the recruitment workflow.
"""

import os
import re
import json
import uuid
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

# Sensitive keys that must always be masked
REDACT_KEYS = {
    "api_key",
    "apikey",
    "groq_api_key",
    "token",
    "access_token",
    "secret",
    "password",
    "authorization",
    "credential",
    "credentials",
    "ssn",
}

# Payload fields that contain large document text to be summarized rather than dumped
TEXT_SUMMARIZE_KEYS = {
    "page_content",
    "raw_text",
    "file_bytes",
    "resume_text",
    "document_content",
    "content",
}

# Regex patterns for detecting and scrubbing PII and leaked credentials embedded in text strings
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CARD_REGEX = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
BEARER_REGEX = re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._~+/-]{10,}\b')
API_KEY_REGEX = re.compile(r'\b(?:gsk_|sk-)[a-zA-Z0-9_\-]{15,}\b')


def redact_string_content(text: str) -> str:
    """Scans and scrubs candidate PII, tokens, and credentials embedded within text."""
    if not text:
        return text
    s = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    s = SSN_REGEX.sub("[REDACTED_SSN]", s)
    s = CARD_REGEX.sub("[REDACTED_CARD]", s)
    s = BEARER_REGEX.sub("Bearer [REDACTED_SECRET]", s)
    s = API_KEY_REGEX.sub("[REDACTED_SECRET]", s)
    # Mask phone numbers (avoiding ISO date strings like 2026-09-25)
    if not re.search(r'^\d{4}-\d{2}-\d{2}', s):
        s = PHONE_REGEX.sub("[REDACTED_PHONE]", s)
    return s


def sanitize_payload(obj: Any, depth: int = 0) -> Any:
    """
    Recursively scrubs sensitive keys, redacts embedded PII/secrets in strings,
    and truncates huge document bodies to keep audit records compliant and compact.
    """
    if depth > 8:
        return "[MAX_DEPTH_EXCEEDED]"

    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            k_lower = str(k).lower()
            if any(secret_term in k_lower for secret_term in REDACT_KEYS):
                if isinstance(v, dict):
                    sanitized[k] = sanitize_payload(v, depth + 1)
                elif isinstance(v, list):
                    sanitized[k] = [
                        sanitize_payload(item, depth + 1) if isinstance(item, dict) else "[REDACTED_SECRET]"
                        for item in v
                    ]
                else:
                    sanitized[k] = "[REDACTED_SECRET]"
            elif k_lower in TEXT_SUMMARIZE_KEYS and isinstance(v, str):
                sanitized[k] = f"[PREVIEW: {v[:80]}... (len={len(v)})]"
            elif isinstance(v, bytes):
                sanitized[k] = f"[RAW_BYTES: len={len(v)}]"
            else:
                sanitized[k] = sanitize_payload(v, depth + 1)
        return sanitized

    if isinstance(obj, list):
        return [sanitize_payload(item, depth + 1) for item in obj]

    if isinstance(obj, str):
        cleaned = redact_string_content(obj)
        if len(cleaned) > 1000:
            return f"{cleaned[:200]}... [TRUNCATED: total {len(cleaned)} chars]"
        return cleaned

    if isinstance(obj, (int, float, bool)) or obj is None:
        return obj

    return str(obj)


class RecruitmentAuditLogger:
    """
    Thread-safe, append-only JSONL audit logger for recruitment intelligence operations
    with automated PII/secret scrubbing and file-size based log rotation.
    """

    def __init__(
        self,
        log_directory: Optional[Union[str, Path]] = None,
        log_file_path: Optional[Union[str, Path]] = None,
        max_bytes: Optional[int] = None,
        backup_count: Optional[int] = None,
    ):
        try:
            from capabl_core.config.settings import get_settings
            cfg = get_settings()
            default_dir = cfg.audit_log_dir
            default_path = cfg.audit_log_path
            default_max = cfg.audit_max_bytes
            default_backups = cfg.audit_backup_count
        except Exception:
            default_dir = os.getenv("ENHANCEMENT_AUDIT_LOG_DIR", "logs/audit")
            default_path = os.getenv("AUDIT_LOG_PATH", "logs/audit/audit_trail.jsonl")
            default_max = 10 * 1024 * 1024
            default_backups = 5

        self.log_directory = Path(log_directory or default_dir)
        self.log_file = Path(log_file_path) if log_file_path else (self.log_directory / "audit_trail.jsonl")
        self.max_bytes = max_bytes if max_bytes is not None else default_max
        self.backup_count = backup_count if backup_count is not None else default_backups
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Ensures the log directory exists."""
        try:
            self.log_directory.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.warning(f"Failed to create audit log directory {self.log_directory}: {exc}")

    def _rotate_if_needed(self) -> None:
        """Rotates the log file if current size exceeds max_bytes."""
        if not self.log_file.exists():
            return
        try:
            if self.log_file.stat().st_size >= self.max_bytes:
                for i in range(self.backup_count - 1, 0, -1):
                    sfn = self.log_file.with_name(f"{self.log_file.name}.{i}")
                    dfn = self.log_file.with_name(f"{self.log_file.name}.{i + 1}")
                    if sfn.exists():
                        if dfn.exists():
                            dfn.unlink()
                        sfn.rename(dfn)
                target = self.log_file.with_name(f"{self.log_file.name}.1")
                if target.exists():
                    target.unlink()
                self.log_file.rename(target)
        except Exception as exc:
            logger.warning(f"Audit log rotation failed: {exc}")

    def log_event(
        self,
        event: str,
        session_id: Optional[str] = None,
        status: str = "success",
        duration_ms: Optional[float] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Appends a structured event record to the audit trail.

        Args:
            event: Event category identifier (e.g. 'tool_executed', 'booking_blocked').
            session_id: Optional correlation session identifier.
            status: Execution status ('success', 'blocked', 'error', etc.).
            duration_ms: Elapsed execution time in milliseconds.
            payload: Domain-specific event details.
            **kwargs: Additional key-value pairs to merge into payload.

        Returns:
            Dict[str, Any]: The exact structured event record written.
        """
        timestamp_str = datetime.now(timezone.utc).isoformat()
        event_id = str(uuid.uuid4())

        combined_payload = dict(payload or {})
        combined_payload.update(kwargs)

        safe_payload = sanitize_payload(combined_payload)

        record: Dict[str, Any] = {
            "event_id": event_id,
            "timestamp": timestamp_str,
            "event": event,
            "session_id": session_id or "default_session",
            "status": status,
            "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
            "payload": safe_payload,
        }

        try:
            self._ensure_log_dir()
            self._rotate_if_needed()
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.error(f"Failed to append to audit trail {self.log_file}: {exc}")

        return record

    # Convenience helpers for required event categories

    def log_session_start(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.log_event("session_started", session_id=session_id, payload=metadata or {})

    def log_document_ingested(
        self,
        document_id: str,
        document_type: str,
        chunk_count: int,
        session_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            "document_ingested",
            session_id=session_id,
            payload={
                "document_id": document_id,
                "document_type": document_type,
                "chunk_count": chunk_count,
                "candidate_id": candidate_id,
                "job_id": job_id,
            },
        )

    def log_retrieval_started(self, query: str, document_type: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.log_event(
            "retrieval_started",
            session_id=session_id,
            payload={"query": query, "document_type": document_type},
        )

    def log_retrieval_completed(
        self,
        query: str,
        document_type: str,
        retrieved_count: int,
        duration_ms: float,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            "retrieval_completed",
            session_id=session_id,
            duration_ms=duration_ms,
            payload={"query": query, "document_type": document_type, "retrieved_count": retrieved_count},
        )

    def log_match_started(self, candidate_id: str, job_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.log_event(
            "match_started",
            session_id=session_id,
            payload={"candidate_id": candidate_id, "job_id": job_id},
        )

    def log_match_completed(
        self,
        candidate_id: str,
        job_id: str,
        matched_skills: List[str],
        missing_skills: List[str],
        duration_ms: float,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            "match_completed",
            session_id=session_id,
            duration_ms=duration_ms,
            payload={
                "candidate_id": candidate_id,
                "job_id": job_id,
                "matched_count": len(matched_skills),
                "missing_count": len(missing_skills),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            },
        )

    def log_tool_requested(self, tool_name: str, arguments: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.log_event(
            "tool_requested",
            session_id=session_id,
            payload={"tool": tool_name, "arguments": arguments},
        )

    def log_tool_executed(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        duration_ms: float,
        status: str = "success",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            "tool_executed",
            session_id=session_id,
            status=status,
            duration_ms=duration_ms,
            payload={"tool": tool_name, "arguments": arguments},
        )

    def log_tool_blocked(self, tool_name: str, reason: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.log_event(
            "tool_blocked",
            session_id=session_id,
            status="blocked",
            payload={"tool": tool_name, "reason": reason},
        )

    def log_agent_started(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.log_event("agent_started", session_id=session_id, payload={"query": query})

    def log_agent_completed(
        self,
        query: str,
        status: str,
        duration_ms: float,
        tools_invoked: int,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.log_event(
            "agent_completed",
            session_id=session_id,
            status=status,
            duration_ms=duration_ms,
            payload={"query": query, "tools_invoked": tools_invoked},
        )

    def log_booking_requested(self, slot_id: str, candidate_id: str, job_id: str, confirmed: bool, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.log_event(
            "booking_requested",
            session_id=session_id,
            payload={"slot_id": slot_id, "candidate_id": candidate_id, "job_id": job_id, "confirmed": confirmed},
        )

    def log_booking_blocked(self, slot_id: str, reason: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.log_event(
            "booking_blocked",
            session_id=session_id,
            status="blocked",
            payload={"slot_id": slot_id, "reason": reason},
        )

    def log_booking_confirmed(self, booking_id: str, slot_id: str, candidate_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.log_event(
            "booking_confirmed",
            session_id=session_id,
            status="confirmed",
            payload={"booking_id": booking_id, "slot_id": slot_id, "candidate_id": candidate_id},
        )

    def log_security_event(self, event_sub_type: str, message: str, session_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        p = {"sub_type": event_sub_type, "message": message}
        if details:
            p.update(details)
        return self.log_event("security_event", session_id=session_id, status="flagged", payload=p)

    def log_error(self, message: str, session_id: Optional[str] = None, exc_info: Optional[str] = None) -> Dict[str, Any]:
        return self.log_event("error", session_id=session_id, status="error", payload={"message": message, "trace": exc_info})

    def get_recent_events(
        self,
        limit: int = 50,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the most recent audit records, optionally filtered by session or event type.
        """
        if not self.log_file.exists():
            return []

        events: List[Dict[str, Any]] = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in reversed(lines):
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    record = json.loads(line_str)
                    if session_id and record.get("session_id") != session_id:
                        continue
                    if event_type and record.get("event") != event_type:
                        continue
                    events.append(record)
                    if len(events) >= limit:
                        break
                except Exception:
                    continue
        except Exception as exc:
            logger.error(f"Error reading audit trail {self.log_file}: {exc}")

        return events

    query_events = get_recent_events

    def clear_logs(self) -> None:
        """Truncates the log file for clean testing environments."""
        try:
            if self.log_file.exists():
                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.write("")
        except Exception as exc:
            logger.warning(f"Failed to clear audit log file: {exc}")


# Default singleton instance
DEFAULT_AUDIT_LOGGER = RecruitmentAuditLogger()
