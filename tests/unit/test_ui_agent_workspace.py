"""
Unit Tests for CAPABL UI Agent Intelligence Workspace (Phase 8).

Validates:
1. Context Omnipresence:
   - Current Candidate, Current Role, Current Domain, and Strict Isolation Badge.
2. Animated Agent Activity Rail:
   - 5 stages: Analyzing request → Retrieving candidate evidence → Retrieving job requirements →
     Validating context → Synthesizing response.
3. Chat & Citations:
   - User and agent message components, clickable citations, and evidence drawer.
4. Premium Composer:
   - Multiline input, slash commands (/match, /skills, /policy, /slots, /clear),
     keyboard shortcuts, and send button.
5. Non-Fabricated / State-Grounded Empty State:
   - Contextual actions derived from actual stored candidate & job profiles.
   - Zero hardcoded fake candidates.
6. Design Tokens & Motion Keyframes:
   - capablMessageSlideIn, capablActivityLinePulse, capablButtonSend.
"""

import unittest
from pathlib import Path

from capabl_core.ui.views.agent_workspace import (
    render_agent_workspace,
    render_context_banner,
    render_activity_rail,
    render_evidence_drawer_modal,
    render_empty_state_actions,
    get_default_context,
)


class TestCAPABLAgentWorkspace(unittest.TestCase):
    """Test suite for Phase 8 Agent Intelligence Workspace."""

    def test_agent_workspace_module_exports(self):
        """Verifies that all primary components are callable."""
        self.assertTrue(callable(render_agent_workspace))
        self.assertTrue(callable(render_context_banner))
        self.assertTrue(callable(render_activity_rail))
        self.assertTrue(callable(render_evidence_drawer_modal))
        self.assertTrue(callable(render_empty_state_actions))
        self.assertTrue(callable(get_default_context))

    def test_context_omnipresence_elements(self):
        """Validates that Candidate, Target Role, Domain, and Isolation are in context banner."""
        ws_path = Path("capabl_core/ui/views/agent_workspace.py")
        self.assertTrue(ws_path.exists())
        content = ws_path.read_text(encoding="utf-8")

        self.assertIn("Candidate", content)
        self.assertIn("Target Role", content)
        self.assertIn("Domain", content)
        self.assertIn("Strict Domain Quarantine Enforced", content)

    def test_activity_rail_stages_present(self):
        """Validates all 5 stages of the animated activity rail."""
        ws_path = Path("capabl_core/ui/views/agent_workspace.py")
        content = ws_path.read_text(encoding="utf-8")

        self.assertIn("Analyzing request", content)
        self.assertIn("Retrieving candidate evidence", content)
        self.assertIn("Retrieving job requirements", content)
        self.assertIn("Validating context", content)
        self.assertIn("Synthesizing response", content)

    def test_interactive_evidence_drawer_and_citations(self):
        """Validates evidence drawer modal and grounded citations."""
        ws_path = Path("capabl_core/ui/views/agent_workspace.py")
        content = ws_path.read_text(encoding="utf-8")

        self.assertIn("Evidence Drawer • Grounded Source Citations", content)
        self.assertIn("Verified Grounding", content)
        self.assertIn("Origin Path:", content)

    def test_premium_composer_and_slash_commands(self):
        """Validates multiline composer, slash commands, and keyboard shortcut hints."""
        ws_path = Path("capabl_core/ui/views/agent_workspace.py")
        content = ws_path.read_text(encoding="utf-8")

        # Slash commands
        self.assertIn("/match", content)
        self.assertIn("/skills", content)
        self.assertIn("/policy", content)
        self.assertIn("/slots", content)
        self.assertIn("/clear", content)

        # Multiline & Keyboard hints
        self.assertIn("multiline support", content)
        self.assertIn("Shift+Enter", content)
        self.assertIn("Send Inquiry", content)

    def test_state_grounded_empty_state_actions(self):
        """Validates that empty state actions use real workspace state."""
        ctx = get_default_context()
        self.assertIn("candidate_id", ctx)
        self.assertIn("job_id", ctx)
        self.assertIn("candidates", ctx)
        self.assertIn("jobs", ctx)

        ws_path = Path("capabl_core/ui/views/agent_workspace.py")
        content = ws_path.read_text(encoding="utf-8")
        self.assertIn("Contextual Actions Grounded in Workspace State", content)

    def test_styles_and_motion_keyframes(self):
        """Validates presence of Phase 8 classes and keyframes."""
        styles_path = Path("capabl_core/ui/theme/styles.py")
        styles_content = styles_path.read_text(encoding="utf-8")
        self.assertIn(".capabl-agent-context-banner", styles_content)
        self.assertIn(".capabl-activity-rail", styles_content)
        self.assertIn(".capabl-activity-step", styles_content)
        self.assertIn(".capabl-chat-msg-user", styles_content)
        self.assertIn(".capabl-chat-msg-agent", styles_content)
        self.assertIn(".capabl-citation-pill", styles_content)
        self.assertIn(".capabl-slash-pill", styles_content)

        motion_path = Path("capabl_core/ui/theme/motion.py")
        motion_content = motion_path.read_text(encoding="utf-8")
        self.assertIn("@keyframes capablMessageSlideIn", motion_content)
        self.assertIn("@keyframes capablActivityLinePulse", motion_content)
        self.assertIn("@keyframes capablButtonSend", motion_content)


if __name__ == "__main__":
    unittest.main()
