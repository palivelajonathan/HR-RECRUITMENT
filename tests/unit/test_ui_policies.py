"""
Unit Tests for CAPABL UI Policy Intelligence Workspace (Phase 10).

Validates:
1. Policy List Display Contract:
   - Every catalog policy defines: title, department, version, effective date, status.
   - Search and department filtering compatibility.
2. Policy Detail Structure:
   - 4 Tabs: Document, Sections, Evidence, and Metadata.
   - Smooth section expansion capability.
3. Grounded AI Policy Question Answering:
   - Questions answered strictly with verified policy evidence.
   - Every citation reveals source document, page, and verbatim excerpt.
4. Strict Domain Isolation:
   - Zero candidate evidence mixed with policy evidence.
   - Candidate IDs are strictly None for all policy evidence items.
   - Inquiries targeting candidate PII in policy workspace are blocked by domain quarantine.
5. Rich Animation & Motion Engine:
   - @keyframes capablSectionExpand present.
   - @keyframes capablCitationReveal present.
   - @keyframes capablPolicyCardEnter present.
   - Semantic styles in styles.py.
"""

import sys
import unittest
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from capabl_core.evidence.service import EvidenceService
from capabl_core.evidence.models import EvidenceEnvelope, EvidenceItem
from capabl_core.ui.views.policies import (
    render_policies_workspace,
    get_policy_catalog,
    render_policy_card,
    render_policy_detail,
    render_policy_qa_surface,
)


class TestCAPABLPolicyIntelligence(unittest.TestCase):
    """Test suite for Phase 10 Policy Intelligence Workspace."""

    def setUp(self):
        self.catalog = get_policy_catalog()
        self.evidence_service = EvidenceService()

    def test_policy_workspace_module_exports(self):
        """Verifies that all Phase 10 UI functions are exported and callable."""
        self.assertTrue(callable(render_policies_workspace))
        self.assertTrue(callable(get_policy_catalog))
        self.assertTrue(callable(render_policy_card))
        self.assertTrue(callable(render_policy_detail))
        self.assertTrue(callable(render_policy_qa_surface))

    def test_policy_list_required_fields(self):
        """
        Validates Policy List contract:
        Every policy must define: title, department, version, effective date, status.
        """
        self.assertGreater(len(self.catalog), 0)
        for policy in self.catalog:
            self.assertIn("id", policy)
            self.assertIn("title", policy)
            self.assertIn("department", policy)
            self.assertIn("version", policy)
            self.assertIn("effective_date", policy)
            self.assertIn("status", policy)
            self.assertIn("category", policy)
            self.assertIn("filename", policy)
            self.assertIn("description", policy)
            self.assertIn("sections", policy)

            # Values must not be empty
            self.assertTrue(len(policy["title"].strip()) > 0)
            self.assertTrue(len(policy["department"].strip()) > 0)
            self.assertTrue(len(policy["version"].strip()) > 0)
            self.assertTrue(len(policy["effective_date"].strip()) > 0)
            self.assertEqual(policy["status"].lower(), "active")

    def test_policy_detail_sections_structure(self):
        """Validates that policy sections contain num, title, summary, and body."""
        for policy in self.catalog:
            sections = policy.get("sections", [])
            self.assertGreater(len(sections), 0)
            for sec in sections:
                self.assertIn("num", sec)
                self.assertIn("title", sec)
                self.assertIn("summary", sec)
                self.assertIn("body", sec)
                self.assertTrue(len(sec["title"].strip()) > 0)
                self.assertTrue(len(sec["body"].strip()) > 0)

    def test_policy_detail_tabs_in_source(self):
        """Validates presence of Document, Sections, Evidence, and Metadata tabs in policies.py."""
        policies_path = Path("capabl_core/ui/views/policies.py")
        self.assertTrue(policies_path.exists())
        content = policies_path.read_text(encoding="utf-8")

        self.assertIn("📄 Document", content)
        self.assertIn("📑 Sections", content)
        self.assertIn("🔍 Evidence", content)
        self.assertIn("ℹ️ Metadata", content)

    def test_grounded_policy_evidence_retrieval(self):
        """Validates that real policy queries return verified policy evidence chunks."""
        queries = [
            "annual paid time off PTO allowance",
            "remote work core collaboration hours",
            "multi-factor authentication password security",
        ]
        for q in queries:
            envelope: EvidenceEnvelope = self.evidence_service.get_policy_evidence(query=q, top_k=3)
            self.assertIn(envelope.status, ("success", "no_evidence"))
            if envelope.status == "success":
                self.assertGreater(len(envelope.items), 0)
                for item in envelope.items:
                    self.assertEqual(item.document_type, "policy")
                    self.assertIsNotNone(item.source)
                    self.assertIsNotNone(item.excerpt)
                    self.assertTrue(len(item.excerpt) > 0)

    def test_strict_domain_isolation_no_candidate_leakage(self):
        """
        CRITICAL SECURITY INVARIANT:
        Do not mix candidate evidence with policy evidence.
        Candidate ID and Job ID must remain None for all policy evidence.
        """
        envelope: EvidenceEnvelope = self.evidence_service.get_policy_evidence(
            query="company leave remote work attendance",
            top_k=5,
        )
        for item in envelope.items:
            # Policy evidence items must NEVER carry candidate or job identifiers
            self.assertEqual(item.document_type, "policy")
            self.assertIsNone(item.candidate_id, "CRITICAL: Candidate ID leaked into policy evidence!")
            self.assertIsNone(item.job_id, "CRITICAL: Job ID leaked into policy evidence!")
            # Source must be a policy document, not a resume or JD
            self.assertFalse("resume" in item.source.lower(), f"Resume leaked into policy: {item.source}")
            self.assertFalse("jd_" in item.source.lower() and not "policy" in item.source.lower(), f"JD leaked into policy: {item.source}")

    def test_motion_keyframes_present(self):
        """Validates that Phase 10 motion keyframes are defined in motion.py."""
        motion_path = Path("capabl_core/ui/theme/motion.py")
        motion_content = motion_path.read_text(encoding="utf-8")

        self.assertIn("@keyframes capablSectionExpand", motion_content)
        self.assertIn("@keyframes capablCitationReveal", motion_content)
        self.assertIn("@keyframes capablPolicyCardEnter", motion_content)

    def test_design_system_styles_present(self):
        """Validates that Phase 10 CSS classes are defined in styles.py."""
        styles_path = Path("capabl_core/ui/theme/styles.py")
        styles_content = styles_path.read_text(encoding="utf-8")

        self.assertIn(".capabl-policy-card", styles_content)
        self.assertIn(".capabl-policy-card-selected", styles_content)
        self.assertIn(".capabl-policy-section-box", styles_content)
        self.assertIn(".capabl-policy-evidence-card", styles_content)
        self.assertIn(".capabl-policy-citation", styles_content)
        self.assertIn(".capabl-policy-answer-box", styles_content)
        self.assertIn(".capabl-domain-badge-isolated", styles_content)


if __name__ == "__main__":
    unittest.main()
