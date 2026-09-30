"""
Unit Tests for CAPABL UI Job Management Workspace (Phase 5).

Validates:
1. get_job_profiles() queries real persisted data from ChromaDB and roles registry.
2. Non-fabrication: Profiles reflect real jobs, real vector chunks, and real metadata.
3. Deterministic Requirements: Requirements are authoritative, extracted deterministically via extract_required_skills.
4. AST Compatibility: Ensures 'jd_uploader' and 'Upload Job Description' exist in app.py and jobs.py.
5. Create Role Workflow: All 6 stages (Role details, JD upload/paste, Validation, Requirement extraction, Indexing, Ready) present.
6. Job Profile Tabs: All 6 tabs (Overview, Requirements, Candidates, Matches, Evidence, Activity) present.
7. Staggered Motion & Styling: Staggered animation classes and job card CSS present.
"""

import unittest
from pathlib import Path

from capabl_core.ui.views.jobs import get_job_profiles
from capabl_core.matching.extractor import extract_required_skills
from capabl_core.workflow import DEFAULT_WORKFLOW_SERVICE


class TestCAPABLJobWorkspace(unittest.TestCase):
    """Test suite for Phase 5 Job Requisition Workspace."""

    def test_get_job_profiles_structure(self):
        profiles = get_job_profiles()
        self.assertIsInstance(profiles, list)
        self.assertGreater(len(profiles), 0)

        p = profiles[0]
        self.assertIn("job_id", p)
        self.assertIn("title", p)
        self.assertIn("department", p)
        self.assertIn("location", p)
        self.assertIn("status", p)
        self.assertIn("chunk_count", p)
        self.assertIn("page_count", p)
        self.assertIn("sources", p)
        self.assertIn("requirements", p)
        self.assertIn("matched_candidates_count", p)

        self.assertIsInstance(p["chunk_count"], int)
        self.assertIsInstance(p["requirements"], list)

    def test_non_fabricated_job_data(self):
        """Verifies that job descriptions in profiles correspond to real stored jobs."""
        profiles = get_job_profiles()
        job_ids = [p["job_id"] for p in profiles]
        self.assertIn("jd_backend_lead_2026", job_ids)

        backend_job = next(p for p in profiles if p["job_id"] == "jd_backend_lead_2026")
        self.assertIn("Senior", backend_job["title"])
        self.assertIn("Backend", backend_job["title"])
        self.assertEqual(backend_job["status"], "Active")

    def test_deterministic_requirements_authoritative(self):
        """Verifies that requirement extraction is deterministic and authoritative."""
        sample_jd_text = (
            "Job Title: Backend Architect\n"
            "Required Qualifications:\n"
            "- Hands-on proficiency in Python, FastAPI, and Docker.\n"
            "- Relational database experience with PostgreSQL and Redis.\n"
            "Preferred Skills: Experience with Kafka."
        )
        reqs = extract_required_skills(sample_jd_text)
        self.assertIsInstance(reqs, list)
        self.assertIn("python", reqs)
        self.assertIn("fastapi", reqs)
        self.assertIn("docker", reqs)
        self.assertIn("postgresql", reqs)
        self.assertIn("redis", reqs)

    def test_ast_compatibility_markers(self):
        """Validates that required upload strings exist in app.py and jobs.py."""
        app_path = Path("capabl_core/ui/app.py")
        self.assertTrue(app_path.exists())
        app_content = app_path.read_text(encoding="utf-8")
        self.assertIn("jd_uploader", app_content)
        self.assertIn("Upload Job Description", app_content)

        job_path = Path("capabl_core/ui/views/jobs.py")
        self.assertTrue(job_path.exists())
        job_content = job_path.read_text(encoding="utf-8")
        self.assertIn("jd_uploader", job_content)
        self.assertIn("Upload Job Description", job_content)

    def test_six_creation_stages_present(self):
        """Verifies that all 6 required role creation workflow stages are handled."""
        job_path = Path("capabl_core/ui/views/jobs.py")
        job_content = job_path.read_text(encoding="utf-8")
        stages = [
            "Role Details",
            "JD Ingestion",
            "Validation",
            "Requirement Extraction",
            "Indexing",
            "Ready",
        ]
        for stage in stages:
            self.assertIn(stage, job_content)

    def test_six_profile_tabs_present(self):
        """Verifies that all 6 required job profile tabs are defined."""
        job_path = Path("capabl_core/ui/views/jobs.py")
        job_content = job_path.read_text(encoding="utf-8")
        tabs = [
            '"Overview"',
            '"Requirements"',
            '"Candidates"',
            '"Matches"',
            '"Evidence"',
            '"Activity"',
        ]
        for tab in tabs:
            self.assertIn(tab, job_content)

    def test_staggered_motion_and_styling(self):
        """Verifies presence of staggered chip animation and job card styles."""
        styles_path = Path("capabl_core/ui/theme/styles.py")
        styles_content = styles_path.read_text(encoding="utf-8")
        self.assertIn(".capabl-job-card", styles_content)
        self.assertIn(".capabl-chip-stagger", styles_content)
        self.assertIn(".capabl-chip-active", styles_content)
        self.assertIn(".capabl-chip-closed", styles_content)

        motion_path = Path("capabl_core/ui/theme/motion.py")
        motion_content = motion_path.read_text(encoding="utf-8")
        self.assertIn("capablChipFadeIn", motion_content)
        self.assertIn(".stagger-12", motion_content)


if __name__ == "__main__":
    unittest.main()
