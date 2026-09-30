"""
Unit Tests for CAPABL UI Production Application Shell (Phase 2).

Validates:
1. Shell Navigation Structure:
   - Primary: Overview, Candidates, Jobs, Matches, Evidence, Interviews, Policies, Analytics.
   - Secondary: Settings, Help.
2. Global Command Palette & Search Index:
   - Candidates, Jobs, Evidence, Interviews, Policies, System Actions.
3. AST & Contract Safeguards:
   - Presence of 'resume_uploader' and 'Upload Candidate Resume'.
   - Presence of 'jd_uploader' and 'Upload Job Description'.
   - Absence of hackathon/demo banners ('Track 6', 'M10 Release Candidate', 'Demo Control & Quick-Start Bar').
   - Clean export of main(), get_cached_agent(), and get_active_provider_name().
"""

import unittest
from pathlib import Path

from capabl_core.ui.shell import (
    render_sidebar,
    render_topbar,
    render_command_palette,
    NAV_PRIMARY,
    NAV_SECONDARY,
)
from capabl_core.ui.shell.command_palette import SEARCH_INDEX
import capabl_core.ui.app as ui_app


class TestCAPABLShellStructure(unittest.TestCase):
    """Test suite for application shell navigation and structure."""

    def test_primary_navigation_items(self):
        nav_keys = [item[0] for item in NAV_PRIMARY]
        expected_keys = [
            "overview",
            "candidates",
            "jobs",
            "matches",
            "evidence",
            "interviews",
            "policies",
            "security",
            "analytics",
        ]
        self.assertEqual(nav_keys, expected_keys)
        self.assertEqual(len(NAV_PRIMARY), 9)

    def test_secondary_navigation_items(self):
        nav_keys = [item[0] for item in NAV_SECONDARY]
        expected_keys = ["settings", "help"]
        self.assertEqual(nav_keys, expected_keys)

    def test_command_palette_search_index(self):
        self.assertGreater(len(SEARCH_INDEX), 5)
        categories = {item["category"] for item in SEARCH_INDEX}
        self.assertTrue(any("Candidates" in c for c in categories))
        self.assertTrue(any("Jobs" in c for c in categories))
        self.assertTrue(any("Evidence" in c for c in categories))
        self.assertTrue(any("Interviews" in c for c in categories))
        self.assertTrue(any("Policies" in c for c in categories))
        self.assertTrue(any("Security" in c for c in categories))

        targets = {item["nav_target"] for item in SEARCH_INDEX}
        self.assertIn("candidates", targets)
        self.assertIn("jobs", targets)
        self.assertIn("matches", targets)
        self.assertIn("evidence", targets)
        self.assertIn("interviews", targets)
        self.assertIn("policies", targets)
        self.assertIn("security", targets)


class TestCAPABLShellContracts(unittest.TestCase):
    """Test suite verifying removal of demo labels and preservation of required AST strings."""

    def setUp(self):
        self.app_path = Path("capabl_core/ui/app.py")
        self.content = self.app_path.read_text(encoding="utf-8")

    def test_required_ast_upload_strings_present(self):
        self.assertIn("resume_uploader", self.content)
        self.assertIn("Upload Candidate Resume", self.content)
        self.assertIn("jd_uploader", self.content)
        self.assertIn("Upload Job Description", self.content)

    def test_hackathon_demo_labels_removed_from_main_content(self):
        self.assertNotIn("Track 6 — HR / Recruitment", self.content)
        self.assertNotIn("M10 Release Candidate", self.content)
        self.assertNotIn("Demo Control & Quick-Start Bar", self.content)
        self.assertNotIn("Quick-Load Demo: Alex Chen", self.content)
        self.assertNotIn("Quick-Load Demo: Priya Sharma", self.content)

    def test_app_module_exports_and_callables(self):
        self.assertTrue(hasattr(ui_app, "main"))
        self.assertTrue(callable(ui_app.main))
        self.assertTrue(hasattr(ui_app, "get_cached_agent"))
        self.assertTrue(hasattr(ui_app, "get_active_provider_name"))


if __name__ == "__main__":
    unittest.main()
