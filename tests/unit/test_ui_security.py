"""
Unit Tests for CAPABL UI Security & Trust Center Workspace (Phase 11).

Validates:
1. Security Workspace Module Exports:
   - render_security_workspace, render_security_status_grid, render_audit_timeline,
     render_event_detail_drawer, render_secret_hygiene_panel.
2. Actual Runtime State for all 6 Pillars:
   - candidate_isolation
   - document_isolation
   - prompt_injection_defense
   - authorization_gates
   - audit_logging
   - mcp_boundary
3. Searchable Audit Timeline & Normalization:
   - Validates that audit events normalize cleanly into:
     timestamp, actor, action, resource, result.
   - Verifies the 5 canonical examples:
     Document uploaded, Evidence retrieved, Tool invoked, Booking attempted, Booking confirmed.
4. Detail Drawer Structure & Required Fields:
   - timestamp, actor, action, resource, result.
   - Zero plaintext secrets or credentials.
5. Strict Redaction Policy & Secret Hygiene:
   - API keys, tokens, credentials, and private environment variables are never exposed.
   - Masked with [CONFIGURED: •••••••• (Masked)] or [NOT_CONFIGURED].
6. Motion & CSS Design System Tokens:
   - @keyframes capablSecurityPulse, capablTimelineNodeEnter, capablSecurityDrawerOpen.
   - .capabl-security-card, .capabl-security-drawer, .capabl-redaction-pill.
"""

import sys
import unittest
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from enhancement.security.audit_logger import DEFAULT_AUDIT_LOGGER
from capabl_core.security.runtime import (
    get_security_runtime_state,
    get_redacted_env_vars,
    normalize_audit_event,
    seed_sample_audit_events_if_needed,
)
from capabl_core.ui.views.security import (
    render_security_workspace,
    render_security_status_grid,
    render_audit_timeline,
    render_event_detail_drawer,
    render_secret_hygiene_panel,
)


class TestCAPABLSecurityTrustCenter(unittest.TestCase):
    """Test suite for Phase 11 Security & Trust Center."""

    @classmethod
    def setUpClass(cls):
        # Ensure sample events are present
        seed_sample_audit_events_if_needed()

    def test_security_workspace_module_exports(self):
        """Verifies that all Phase 11 UI functions are exported and callable."""
        self.assertTrue(callable(render_security_workspace))
        self.assertTrue(callable(render_security_status_grid))
        self.assertTrue(callable(render_audit_timeline))
        self.assertTrue(callable(render_event_detail_drawer))
        self.assertTrue(callable(render_secret_hygiene_panel))

    def test_runtime_state_six_pillars(self):
        """
        Validates that get_security_runtime_state() executes real probes across
        all 6 required pillars:
        - Candidate isolation
        - Document isolation
        - Prompt injection defense
        - Authorization gates
        - Audit logging
        - MCP boundary
        """
        state = get_security_runtime_state()
        self.assertIn("timestamp", state)
        self.assertIn("pillars", state)

        pillars = state["pillars"]
        required_pillars = [
            "candidate_isolation",
            "document_isolation",
            "prompt_injection_defense",
            "authorization_gates",
            "audit_logging",
            "mcp_boundary",
        ]

        for p_key in required_pillars:
            self.assertIn(p_key, pillars, f"Missing required pillar: {p_key}")
            p_data = pillars[p_key]
            self.assertIn("name", p_data)
            self.assertIn("status", p_data)
            self.assertIn("metric", p_data)
            self.assertIn("details", p_data)
            self.assertIn("verified", p_data)
            self.assertIn("latency_ms", p_data)

            # Values must be non-empty and verified
            self.assertTrue(len(p_data["name"]) > 0)
            self.assertTrue(len(p_data["status"]) > 0)
            self.assertTrue(len(p_data["metric"]) > 0)
            self.assertTrue(len(p_data["details"]) > 0)
            self.assertTrue(p_data["verified"], f"Pillar probe failed: {p_key}")
            self.assertGreaterEqual(p_data["latency_ms"], 0.0)

    def test_audit_event_normalization_detail_drawer_contract(self):
        """
        Validates Detail View contract:
        Clicking an event must open a detailed drawer showing:
        - timestamp
        - actor
        - action
        - resource
        - result
        """
        sample_raw = {
            "event_id": "test-uuid-12345",
            "timestamp": "2026-09-29T21:45:00.123456+00:00",
            "event": "booking_confirmed",
            "session_id": "sess_recruiter_01",
            "status": "confirmed",
            "duration_ms": 18.4,
            "payload": {
                "booking_id": "book_001",
                "slot_id": "slot_100",
                "candidate_id": "alex_chen",
                "confirmed": True,
            },
        }

        norm = normalize_audit_event(sample_raw)

        # 5 required fields
        self.assertIn("timestamp", norm)
        self.assertIn("actor", norm)
        self.assertIn("action", norm)
        self.assertIn("resource", norm)
        self.assertIn("result", norm)

        # Detailed checks
        self.assertTrue(len(norm["timestamp"]) > 0)
        self.assertTrue(len(norm["actor"]) > 0)
        self.assertEqual(norm["action"], "Booking Confirmed")
        self.assertIn("alex_chen", norm["resource"])
        self.assertTrue(len(norm["result"]) > 0)
        self.assertTrue(norm["redaction_verified"])

    def test_canonical_audit_examples_present(self):
        """
        Validates that the audit timeline contains all 5 required canonical examples:
        - Document uploaded
        - Evidence retrieved
        - Tool invoked
        - Booking attempted
        - Booking confirmed
        """
        events = DEFAULT_AUDIT_LOGGER.query_events(limit=100)
        self.assertGreater(len(events), 0)

        normalized = [normalize_audit_event(e) for e in events]
        actions = {e["action"] for e in normalized}

        self.assertIn("Document Uploaded", actions)
        self.assertIn("Evidence Retrieved", actions)
        self.assertIn("Tool Invoked", actions)
        self.assertIn("Booking Attempted", actions)
        self.assertIn("Booking Confirmed", actions)

    def test_strict_redaction_no_secrets_exposed(self):
        """
        CRITICAL SECURITY INVARIANT:
        Do not expose secrets.
        Never show:
        API keys, tokens, credentials, private environment variables.
        """
        env_vars = get_redacted_env_vars()
        self.assertGreater(len(env_vars), 0)

        for item in env_vars:
            val = item["value"]
            is_sec = item["is_secret"]

            # Must NEVER contain live API key patterns
            self.assertNotIn("sk-", val)
            self.assertNotIn("gsk_", val)
            self.assertNotIn("Bearer ", val)

            if is_sec == "true":
                # Confidential credentials must be safely masked
                self.assertTrue(
                    val in ("[CONFIGURED: •••••••• (Masked)]", "[NOT_CONFIGURED]"),
                    f"Secret variable '{item['variable']}' was exposed: {val}",
                )

    def test_payload_redaction_scrubbing(self):
        """Verifies that sensitive keys in audit event payloads are scrubbed."""
        adversarial_event = {
            "event_id": "test-sec-leak",
            "timestamp": "2026-09-29T21:45:00+00:00",
            "event": "tool_executed",
            "session_id": "sess_leak",
            "status": "success",
            "duration_ms": 12.0,
            "payload": {
                "groq_api_key": "gsk_live_secret_token_1234567890",
                "authorization": "Bearer sk-secret_bearer_token",
                "password": "SuperSecretPassword123!",
                "candidate_phone": "415-555-0199",
                "candidate_email": "candidate@secret.org",
                "safe_field": "Candidate interview scheduled",
            },
        }

        norm = normalize_audit_event(adversarial_event)
        safe_p = norm["payload"]

        self.assertEqual(safe_p["groq_api_key"], "[REDACTED_SECRET]")
        self.assertEqual(safe_p["authorization"], "[REDACTED_SECRET]")
        self.assertEqual(safe_p["password"], "[REDACTED_SECRET]")
        self.assertNotIn("gsk_live_secret", str(safe_p))
        self.assertNotIn("sk-secret", str(safe_p))
        self.assertNotIn("SuperSecretPassword", str(safe_p))

    def test_motion_keyframes_present(self):
        """Validates that Phase 11 motion keyframes are defined in motion.py."""
        motion_path = Path("capabl_core/ui/theme/motion.py")
        motion_content = motion_path.read_text(encoding="utf-8")

        self.assertIn("@keyframes capablSecurityPulse", motion_content)
        self.assertIn("@keyframes capablTimelineNodeEnter", motion_content)
        self.assertIn("@keyframes capablSecurityDrawerOpen", motion_content)

    def test_design_system_styles_present(self):
        """Validates that Phase 11 CSS classes are defined in styles.py."""
        styles_path = Path("capabl_core/ui/theme/styles.py")
        styles_content = styles_path.read_text(encoding="utf-8")

        self.assertIn(".capabl-security-card", styles_content)
        self.assertIn(".capabl-security-drawer", styles_content)
        self.assertIn(".capabl-audit-timeline-container", styles_content)
        self.assertIn(".capabl-audit-event-row", styles_content)
        self.assertIn(".capabl-redaction-pill", styles_content)


if __name__ == "__main__":
    unittest.main()
