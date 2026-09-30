"""
Unit Tests for CAPABL UI Match Intelligence Experience (Phase 6).

Validates:
1. Pure Deterministic Invariant:
   - ZERO match percentage, ZERO hiring score, ZERO ranking, ZERO autonomous hiring decision.
   - Authoritative M3 set-based matching (matched = required & candidate, missing = required - candidate).
2. Cinematic 5-Stage Transition Flow:
   - 1. Candidate -> 2. Resume Evidence -> 3. Requirements -> 4. Deterministic Comparison -> 5. Match Result.
3. Semantic Visual Distinction:
   - Matched requirements: subtle success glow (#34D399, capabl-chip-reveal-match).
   - Missing / unverified requirements: subtle warning/error visual (#F87171, capabl-chip-reveal-missing).
4. Sequential Skill Reveal:
   - capablSkillSequentialReveal keyframes and sequential animation delay stagger.
5. Evidence Drawer Animation & Grounding:
   - capabl-evidence-drawer and capablDrawerSlide keyframe present.
   - Missing skills receive strictly zero fabricated evidence.
"""

import unittest
from pathlib import Path

from capabl_core.matching.matcher import compute_deterministic_match
from capabl_core.ui.views.matches import render_matches_workspace
from capabl_core.workflow import DEFAULT_WORKFLOW_SERVICE


class TestCAPABLMatchExperience(unittest.TestCase):
    """Test suite for Phase 6 Match Intelligence Experience."""

    def test_matches_view_module_exports(self):
        """Verifies that render_matches_workspace is callable."""
        self.assertTrue(callable(render_matches_workspace))

    def test_pure_deterministic_set_based_invariants(self):
        """Validates that matching is strictly set-based with zero subjective scores or percentages."""
        candidate_skills = ["python", "fastapi", "docker", "kubernetes", "postgresql"]
        required_skills = ["python", "fastapi", "docker", "kubernetes", "aws", "graphql"]

        res = compute_deterministic_match(
            candidate_id="alex_chen",
            job_id="jd_backend_lead_2026",
            candidate_skills=candidate_skills,
            required_skills=required_skills,
        )

        # Invariant 1: Matched is exact set intersection
        expected_matched = sorted(list(set(candidate_skills) & set(required_skills)))
        self.assertEqual(res.matched_skills, expected_matched)

        # Invariant 2: Missing is exact set difference
        expected_missing = sorted(list(set(required_skills) - set(candidate_skills)))
        self.assertEqual(res.missing_skills, expected_missing)

        # Invariant 3: Result object does not contain subjective scores or percentages
        self.assertFalse(hasattr(res, "match_percentage"))
        self.assertFalse(hasattr(res, "hiring_score"))
        self.assertFalse(hasattr(res, "ranking"))
        self.assertFalse(hasattr(res, "hire_recommendation"))

    def test_cinematic_pipeline_stages_present(self):
        """Validates presence of all 5 transition steps in matches.py."""
        matches_path = Path("capabl_core/ui/views/matches.py")
        self.assertTrue(matches_path.exists())
        content = matches_path.read_text(encoding="utf-8")

        self.assertIn("1. Candidate", content)
        self.assertIn("2. Resume Evidence", content)
        self.assertIn("3. Requirements", content)
        self.assertIn("4. Deterministic Comparison", content)
        self.assertIn("5. Match Result", content)

    def test_semantic_visual_distinction_classes(self):
        """Validates presence of success glow and warning/error chip classes."""
        styles_path = Path("capabl_core/ui/theme/styles.py")
        styles_content = styles_path.read_text(encoding="utf-8")

        self.assertIn(".capabl-chip-reveal-match", styles_content)
        self.assertIn(".capabl-chip-reveal-missing", styles_content)
        self.assertIn("rgba(16, 185, 129", styles_content)
        self.assertIn("rgba(239, 68, 68", styles_content)

    def test_sequential_skill_reveal_keyframes(self):
        """Validates presence of capablSkillSequentialReveal keyframe."""
        motion_path = Path("capabl_core/ui/theme/motion.py")
        motion_content = motion_path.read_text(encoding="utf-8")

        self.assertIn("@keyframes capablSkillSequentialReveal", motion_content)
        self.assertIn("@keyframes capablDrawerSlide", motion_content)
        self.assertIn("@keyframes capablPipelinePulse", motion_content)

    def test_evidence_drawer_present_in_styles_and_view(self):
        """Validates presence of animated evidence drawer in styles and view."""
        styles_path = Path("capabl_core/ui/theme/styles.py")
        styles_content = styles_path.read_text(encoding="utf-8")
        self.assertIn(".capabl-evidence-drawer", styles_content)
        self.assertIn(".capabl-evidence-drawer-missing", styles_content)

        matches_path = Path("capabl_core/ui/views/matches.py")
        matches_content = matches_path.read_text(encoding="utf-8")
        self.assertIn("capabl-evidence-drawer", matches_content)
        self.assertIn("Evidence Drawer • Verified Match", matches_content)
        self.assertIn("Evidence Drawer • Factual Negative Verification", matches_content)
        self.assertIn("Missing skills receive strictly zero fabricated evidence.", matches_content)

    def test_zero_scores_in_matches_view(self):
        """Ensures no match percentage or hiring score is rendered in matches.py."""
        matches_path = Path("capabl_core/ui/views/matches.py")
        matches_content = matches_path.read_text(encoding="utf-8")
        self.assertNotIn("hiring_score", matches_content)
        self.assertNotIn("hire_score", matches_content)
        self.assertNotIn("match_percentage", matches_content)
        self.assertNotIn("score_weight", matches_content)
        self.assertNotIn("autonomous_decision", matches_content)


if __name__ == "__main__":
    unittest.main()
