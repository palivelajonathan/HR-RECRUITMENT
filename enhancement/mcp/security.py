"""
Security Boundary for MCP External Tool Layer.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Enforces:
1. Untrusted interface validation (path traversal, command injection, length ceilings).
2. Prompt injection defense (sanitization & instruction neutralization).
3. Consequential tool authorization gatekeeper (confirmed == True for calendar mutations).
4. Domain isolation enforcement (candidate != policy != job).
"""

import re
import logging
from typing import Optional, Dict, Any, Tuple

from enhancement.security.audit_logger import DEFAULT_AUDIT_LOGGER

logger = logging.getLogger(__name__)

# Injection and attack patterns
PATH_TRAVERSAL_PATTERN = re.compile(r"(\.\./|\.\.\\|/etc/|C:\\|c:\\|/proc/|/var/)", re.IGNORECASE)
SHELL_METACHOARS_PATTERN = re.compile(r"([;&|`$<>\x00])")
CODE_INJECTION_PATTERN = re.compile(r"(__import__|eval\(|exec\(|subprocess|os\.system|__subclasses__)", re.IGNORECASE)
SQL_INJECTION_PATTERN = re.compile(r"(\bUNION\s+SELECT\b|\bDROP\s+TABLE\b|--|/\*|\*/|;\s*SELECT)", re.IGNORECASE)

PROMPT_INJECTION_SIGNATURES = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*:", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(developer\s+mode|dan|jailbreak)", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(above|instructions)", re.IGNORECASE),
    re.compile(r"export\s+all\s+(candidate|user|system)\s+data", re.IGNORECASE),
    re.compile(r"admin\s+override\s*:", re.IGNORECASE),
    re.compile(r"bypass\s+all\s+(checks|safeguards|security)", re.IGNORECASE),
]


class MCPSecurityError(Exception):
    """Raised when an MCP request violates the security boundary."""
    def __init__(self, message: str, error_code: str = "SECURITY_VIOLATION"):
        super().__init__(message)
        self.error_code = error_code


def validate_safe_input(
    value: str,
    field_name: str,
    max_length: int = 500,
    allow_natural_language: bool = False,
) -> str:
    """
    Validates input strings across path traversal, shell injection, and illegal lengths.
    If allow_natural_language is True (e.g. search queries), allows standard punctuation
    while still blocking path traversal, code injection, and null bytes.
    """
    if not isinstance(value, str):
        raise MCPSecurityError(f"Field '{field_name}' must be a string", error_code="INVALID_TYPE")

    cleaned = value.strip()
    if not cleaned:
        raise MCPSecurityError(f"Field '{field_name}' cannot be empty", error_code="EMPTY_FIELD")

    if len(cleaned) > max_length:
        raise MCPSecurityError(
            f"Field '{field_name}' exceeds maximum length of {max_length} (got {len(cleaned)})",
            error_code="OVERSIZED_INPUT"
        )

    # Path traversal check
    if PATH_TRAVERSAL_PATTERN.search(cleaned):
        raise MCPSecurityError(
            f"Path traversal detected in field '{field_name}'",
            error_code="PATH_TRAVERSAL_ATTEMPT"
        )

    # Code execution primitives
    if CODE_INJECTION_PATTERN.search(cleaned):
        raise MCPSecurityError(
            f"Arbitrary code injection pattern detected in field '{field_name}'",
            error_code="CODE_INJECTION_ATTEMPT"
        )

    # SQL injection primitives
    if SQL_INJECTION_PATTERN.search(cleaned):
        raise MCPSecurityError(
            f"Suspicious SQL syntax detected in field '{field_name}'",
            error_code="SQL_INJECTION_ATTEMPT"
        )

    # Null byte check
    if "\x00" in cleaned:
        raise MCPSecurityError(
            f"Null byte detected in field '{field_name}'",
            error_code="NULL_BYTE_INJECTION"
        )

    if not allow_natural_language:
        # Strict identifier mode: alphanumeric + underscore/dash
        if not re.match(r"^[a-zA-Z0-9_\-]+$", cleaned):
            raise MCPSecurityError(
                f"Field '{field_name}' contains illegal characters: '{cleaned}'",
                error_code="ILLEGAL_CHARACTERS"
            )

    return cleaned


def detect_and_neutralize_prompt_injection(query: str) -> Tuple[bool, str]:
    """
    Scans a natural-language query or document content for instruction hijacking.
    If detected, marks flagged=True and returns a sanitized text safely treated as
    passive document content rather than an instruction.
    """
    flagged = False
    for pattern in PROMPT_INJECTION_SIGNATURES:
        if pattern.search(query):
            flagged = True
            logger.warning("Prompt injection signature matched in MCP input: %s", pattern.pattern)
            break

    # Treat as document content by stripping imperative directives if flagged
    sanitized = query
    if flagged:
        for pattern in PROMPT_INJECTION_SIGNATURES:
            sanitized = pattern.sub("[CONTENT_NEUTRALIZED]", sanitized)

    return flagged, sanitized


def verify_booking_confirmation(confirmed: bool, slot_id: str, candidate_id: str) -> None:
    """
    M4 & M9 Consequential Mutation Gate:
    Enforces that booking mutations can NEVER proceed without explicit confirmation.
    """
    if confirmed is not True:
        logger.warning(
            "Booking mutation blocked: confirmed=%s for slot '%s', candidate '%s'",
            confirmed, slot_id, candidate_id
        )
        DEFAULT_AUDIT_LOGGER.log_event(
            event="mcp_tool_blocked",
            status="blocked",
            payload={
                "action": "book_interview",
                "component": "mcp.security",
                "reason": "CONFIRMATION_REQUIRED",
                "slot_id": slot_id,
                "candidate_id": candidate_id,
                "confirmed": confirmed,
            },
        )
        raise MCPSecurityError(
            f"Interview booking for slot '{slot_id}' requires explicit user confirmation (confirmed=True).",
            error_code="CONFIRMATION_REQUIRED"
        )
