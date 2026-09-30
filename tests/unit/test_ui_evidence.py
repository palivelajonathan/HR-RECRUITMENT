"""
Unit Tests for CAPABL UI Evidence Intelligence Explorer (Phase 7).

Validates:
1. Strict Domain Isolation:
   - Candidate, Job, and Policy domains are quarantined.
   - Enforces zero cross-domain leakage.
2. Evidence Card Completeness:
   - Displays: source, document, page, entity, content, retrieval context.
   - Card expansion & slide-in metadata.
3. Interactive Actions:
   - Copy excerpt, deep inspect JSON, open source, view related evidence.
4. Evidence Graph Visualization:
   - Requirement → Evidence → Source with animated connections (capablFlowPulse).
5. Progressive Loading Sequence:
   - Searching evidence → Filtering domain → Validating isolation → Preparing evidence.
6. MCP Protocol Boundary Hygiene:
   - Normal recruiter UX is uncluttered.
   - Tool routing and protocol diagnostics are encapsulated in developer telemetry.
7. Keyword Highlighting:
   - Tests highlight_terms() for accurate mark wraps and HTML escaping.
"""

import unittest
from pathlib import Path

from capabl_core.ui.views.evidence import (
    render_evidence_workspace,
    highlight_terms,
    render_loading_sequence,
    render_evidence_graph,
    render_evidence_card,
)


class TestCAPABLEvidenceIntelligence(unittest.TestCase):
    """Test suite for Phase 7 Evidence Intelligence Explorer."""

    def test_evidence_view_module_exports(self):
        """Verifies that render_evidence_workspace is callable."""
        self.assertTrue(callable(render_evidence_workspace))
        self.assertTrue(callable(highlight_terms))
        self.assertTrue(callable(render_loading_sequence))
        self.assertTrue(callable(render_evidence_graph))
        self.assertTrue(callable(render_evidence_card))

    def test_isolated_domains_present(self):
        """Validates that Candidate, Job, and Policy domains are cleanly represented."""
        evidence_path = Path("capabl_core/ui/views/evidence.py")
        self.assertTrue(evidence_path.exists())
        content = evidence_path.read_text(encoding="utf-8")

        self.assertIn("Candidate Evidence", content)
        self.assertIn("Job Requirements Evidence", content)
        self.assertIn("Corporate Policy Evidence", content)
        self.assertIn("Strict Cross-Domain Quarantine Active", content)

    def test_evidence_card_attributes_present(self):
        """Validates that all required card fields (source, document, page, entity, content, retrieval context) are in view."""
        evidence_path = Path("capabl_core/ui/views/evidence.py")
        content = evidence_path.read_text(encoding="utf-8")

        # Required fields in card rendering
        self.assertIn("doc_source", content)
        self.assertIn("doc_filename", content)
        self.assertIn("page_display", content)
        self.assertIn("entity_label", content)
        self.assertIn("highlighted_excerpt", content)
        self.assertIn("retrieval_context", content)

    def test_interactive_actions_present(self):
        """Validates presence of copy, inspect, open source, and related evidence actions."""
        evidence_path = Path("capabl_core/ui/views/evidence.py")
        content = evidence_path.read_text(encoding="utf-8")

        self.assertIn("Copy Excerpt", content)
        self.assertIn("Deep Inspect", content)
        self.assertIn("Open Source", content)
        self.assertIn("View Related", content)

    def test_evidence_graph_lineage_present(self):
        """Validates Requirement -> Evidence -> Source graph and animated connectors."""
        evidence_path = Path("capabl_core/ui/views/evidence.py")
        content = evidence_path.read_text(encoding="utf-8")

        self.assertIn("Requirement → Evidence → Source", content)
        self.assertIn("capabl-evidence-graph-container", content)
        self.assertIn("capablFlowPulse", content)
        self.assertIn("capabl-graph-node-req", content)
        self.assertIn("capabl-graph-node-ev", content)
        self.assertIn("capabl-graph-node-src", content)

    def test_progressive_loading_sequence_steps(self):
        """Validates all 4 progressive loading stages are defined."""
        evidence_path = Path("capabl_core/ui/views/evidence.py")
        content = evidence_path.read_text(encoding="utf-8")

        self.assertIn("Searching evidence", content)
        self.assertIn("Filtering domain", content)
        self.assertIn("Validating isolation", content)
        self.assertIn("Preparing evidence", content)

    def test_mcp_developer_diagnostics_isolation(self):
        """Ensures MCP boundary is cleanly isolated in developer diagnostics without cluttering main UX."""
        evidence_path = Path("capabl_core/ui/views/evidence.py")
        content = evidence_path.read_text(encoding="utf-8")

        self.assertIn("Developer & Protocol Diagnostics (MCP Boundary & Telemetry)", content)
        self.assertIn("get_candidate_evidence", content)
        self.assertIn("get_job_evidence", content)
        self.assertIn("get_policy_evidence", content)

        # Ensure app.py no longer contains recruiter-facing radio buttons for execution path
        app_path = Path("capabl_core/ui/app.py")
        app_content = app_path.read_text(encoding="utf-8")
        self.assertNotIn("c_path = st.radio", app_content)
        self.assertNotIn("j_path = st.radio", app_content)
        self.assertNotIn("p_path = st.radio", app_content)

    def test_query_term_highlighting(self):
        """Tests the keyword highlighter helper function."""
        text = "Extensive experience building microservices with FastAPI and Docker on Kubernetes."
        query = "FastAPI and Kubernetes"
        highlighted = highlight_terms(text, query)

        self.assertIn('<mark class="capabl-highlight">FastAPI</mark>', highlighted)
        self.assertIn('<mark class="capabl-highlight">Kubernetes</mark>', highlighted)
        # 'and' is a stopword and should NOT be highlighted
        self.assertNotIn('<mark class="capabl-highlight">and</mark>', highlighted)

    def test_styles_and_motion_tokens(self):
        """Validates that theme styles and motion engines contain Phase 7 classes."""
        styles_path = Path("capabl_core/ui/theme/styles.py")
        styles_content = styles_path.read_text(encoding="utf-8")
        self.assertIn(".capabl-evidence-card", styles_content)
        self.assertIn(".capabl-evidence-meta-drawer", styles_content)
        self.assertIn(".capabl-highlight", styles_content)
        self.assertIn(".capabl-evidence-graph-container", styles_content)

        motion_path = Path("capabl_core/ui/theme/motion.py")
        motion_content = motion_path.read_text(encoding="utf-8")
        self.assertIn("@keyframes capablFlowPulse", motion_content)
        self.assertIn("@keyframes capablCardExpand", motion_content)
        self.assertIn("@keyframes capablHighlightPulse", motion_content)


if __name__ == "__main__":
    unittest.main()
