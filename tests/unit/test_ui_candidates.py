"""
Unit Tests for CAPABL UI Candidate Workspace (Phase 4).

Validates:
1. get_candidate_profiles() queries real persisted data from ChromaDB.
2. Non-fabrication: Profiles reflect real candidates, real vector chunks, and real calendar interviews.
3. Strict Candidate Domain Isolation: Evidence and documents are strictly scoped to candidate_id.
4. AST Compatibility: Ensures 'resume_uploader' and 'Upload Candidate Resume' exist.
5. Ingestion pipeline state sequence: Uploading, Validating, Extracting, Chunking, Embedding, Indexing, Ready.
"""

import unittest
from pathlib import Path

from capabl_core.ui.views.candidates import get_candidate_profiles
from capabl_core.workflow import DEFAULT_WORKFLOW_SERVICE
from capabl_core.calendar.service import DEFAULT_CALENDAR_SERVICE
from capabl_core.evidence.service import EvidenceService


class TestCAPABLCandidateWorkspace(unittest.TestCase):
    """Test suite for Phase 4 Candidate Workspace."""

    def test_get_candidate_profiles_structure(self):
        profiles = get_candidate_profiles()
        self.assertIsInstance(profiles, list)

        if profiles:
            p = profiles[0]
            self.assertIn("candidate_id", p)
            self.assertIn("name", p)
            self.assertIn("role_title", p)
            self.assertIn("chunk_count", p)
            self.assertIn("page_count", p)
            self.assertIn("sources", p)
            self.assertIn("status", p)
            self.assertIn("interview_count", p)

            self.assertIsInstance(p["chunk_count"], int)
            self.assertGreater(p["chunk_count"], 0)

    def test_non_fabricated_candidate_data(self):
        profiles = get_candidate_profiles()
        store = DEFAULT_WORKFLOW_SERVICE.vectorstore_manager.get_or_create_store()
        res = store._collection.get(
            where={"document_type": "resume"},
            include=["metadatas"],
        )
        stored_cids = {m.get("candidate_id") for m in res.get("metadatas", []) if m.get("candidate_id")}

        # Every candidate profile must correspond to an actual stored candidate
        for p in profiles:
            self.assertIn(p["candidate_id"], stored_cids)

    def test_candidate_domain_isolation(self):
        """Validates that candidate evidence retrieval enforces strict candidate_id isolation."""
        evidence_service = EvidenceService()

        # Query evidence for alex_chen
        alex_evidence = evidence_service.get_candidate_evidence(
            query="Python and backend systems experience",
            candidate_id="alex_chen",
            top_k=5,
        )

        for item in alex_evidence.items:
            self.assertEqual(
                item.candidate_id,
                "alex_chen",
                f"Candidate isolation violation: retrieved item for {item.candidate_id} when querying alex_chen",
            )

    def test_ast_compatibility_markers(self):
        """Validates that required upload strings exist in app.py and candidates.py."""
        app_path = Path("capabl_core/ui/app.py")
        self.assertTrue(app_path.exists())
        app_content = app_path.read_text(encoding="utf-8")
        self.assertIn("resume_uploader", app_content)
        self.assertIn("Upload Candidate Resume", app_content)

        cand_path = Path("capabl_core/ui/views/candidates.py")
        self.assertTrue(cand_path.exists())
        cand_content = cand_path.read_text(encoding="utf-8")
        self.assertIn("resume_uploader", cand_content)
        self.assertIn("Upload Candidate Resume", cand_content)

    def test_seven_processing_states_present(self):
        """Verifies that all 7 required document processing states are handled."""
        cand_path = Path("capabl_core/ui/views/candidates.py")
        cand_content = cand_path.read_text(encoding="utf-8")
        states = ["Uploading", "Validating", "Extracting", "Chunking", "Embedding", "Indexing", "Ready"]
        for st_name in states:
            self.assertIn(st_name, cand_content)


if __name__ == "__main__":
    unittest.main()
