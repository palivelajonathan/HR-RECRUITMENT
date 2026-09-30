"""
Unit and Integration Tests for Milestone 6.5: Audit Remediation and System Stabilization.

Covers:
1. Provider: get_active_provider_name() implementation, Ollama/Groq reporting, no silent fallback.
2. UI: Real module import execution of capabl_core.ui.app.
3. PDF Ingestion: Real PDF loading via PyPDFLoader, source_override support, metadata preservation, chunking.
4. Automatic Workflow: Real ingest_document() with PDF files and bytes, automatic match triggering,
   parity with direct run_match(), replacement via ingest_document(..., replace=True), candidate isolation.
5. Configuration: Explicit dependency declarations and qwen3:8b model alignment across infra configs.
6. System Contract: Documentation reflection of deterministic set-based matching.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from capabl_core.llm import (
    LLMProvider,
    LLMConfig,
    LLMConfigError,
    get_active_provider_name,
)
from capabl_core.ingestion.pdf_loader import (
    PDFIngestionPipeline,
    DocumentType,
)
from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.rag.retriever import RecruitmentRetriever
from capabl_core.workflow.service import AutomaticMatchService
from capabl_core.workflow.models import AutomaticMatchResult
from capabl_core.matching.matcher import run_match


class TestM65Remediation(unittest.TestCase):
    """Milestone 6.5 Remediation & Integration Test Suite."""

    @classmethod
    def setUpClass(cls):
        cls.sample_dir = Path("./data/sample")
        cls.resume_alex_path = cls.sample_dir / "resumes" / "resume_alex_chen.pdf"
        cls.resume_priya_path = cls.sample_dir / "resumes" / "resume_priya_sharma.pdf"
        cls.jd_path = cls.sample_dir / "job_descriptions" / "jd_senior_backend_lead.pdf"
        cls.policy_path = cls.sample_dir / "policies" / "policy_leave_and_attendance.pdf"

        assert cls.resume_alex_path.exists(), "Sample resume_alex_chen.pdf missing!"
        assert cls.resume_priya_path.exists(), "Sample resume_priya_sharma.pdf missing!"
        assert cls.jd_path.exists(), "Sample jd_senior_backend_lead.pdf missing!"
        assert cls.policy_path.exists(), "Sample policy_leave_and_attendance.pdf missing!"

    def setUp(self):
        """Create fresh isolated Chroma vector store and workflow service."""
        self.test_dir = tempfile.mkdtemp()
        self.vectorstore_manager = ChromaVectorStoreManager(
            persist_directory=self.test_dir,
            collection_name="test_m6_5_remediation",
        )
        self.retriever = RecruitmentRetriever(vectorstore_or_manager=self.vectorstore_manager)
        self.pipeline = PDFIngestionPipeline()
        self.service = AutomaticMatchService(
            vectorstore_manager=self.vectorstore_manager,
            retriever=self.retriever,
            ingestion_pipeline=self.pipeline,
        )

    def tearDown(self):
        """Clean up temporary test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # --------------------------------------------------------------------------
    # 1. Provider Remediation Tests
    # --------------------------------------------------------------------------

    def test_01_get_active_provider_name_exists_and_callable(self):
        """Test get_active_provider_name is exported and returns a string."""
        provider = get_active_provider_name()
        self.assertIsInstance(provider, str)
        self.assertIn(provider, [p.value for p in LLMProvider])

    def test_02_get_active_provider_name_reports_ollama(self):
        """Test get_active_provider_name accurately reports 'ollama' when configured."""
        cfg = LLMConfig(provider="ollama")
        self.assertEqual(get_active_provider_name(config=cfg), "ollama")

    def test_03_get_active_provider_name_reports_groq(self):
        """Test get_active_provider_name accurately reports 'groq' when configured."""
        cfg = LLMConfig(provider="groq")
        self.assertEqual(get_active_provider_name(config=cfg), "groq")

    def test_04_get_active_provider_name_prohibits_silent_fallback(self):
        """Test get_active_provider_name raises LLMConfigError on invalid provider."""
        cfg = LLMConfig(provider="unsupported_backend")
        with self.assertRaises(LLMConfigError):
            get_active_provider_name(config=cfg)

    # --------------------------------------------------------------------------
    # 2. UI Import & Dependency Resolution Tests
    # --------------------------------------------------------------------------

    def test_05_capabl_ui_app_imports_successfully(self):
        """Test that capabl_core.ui.app module actually imports without ImportError."""
        import capabl_core.ui.app as ui_app
        self.assertTrue(hasattr(ui_app, "main"))
        self.assertTrue(callable(ui_app.main))

    def test_06_ui_dependencies_and_get_cached_agent_defined(self):
        """Test UI helper functions and cached agent definition."""
        import capabl_core.ui.app as ui_app
        self.assertTrue(hasattr(ui_app, "get_cached_agent"))
        self.assertTrue(hasattr(ui_app, "get_active_provider_name"))

    # --------------------------------------------------------------------------
    # 3. Real PDF Ingestion & source_override Tests
    # --------------------------------------------------------------------------

    def test_07_real_pdf_loads_through_pypdfloader(self):
        """Test loading a real sample PDF using PDFIngestionPipeline."""
        docs = self.pipeline.load_pdf(
            file_path=self.resume_alex_path,
            document_type=DocumentType.RESUME,
            document_id="alex_chen",
            candidate_id="alex_chen",
        )
        self.assertGreater(len(docs), 0)
        self.assertEqual(docs[0].metadata["document_type"], "resume")
        self.assertEqual(docs[0].metadata["candidate_id"], "alex_chen")
        self.assertEqual(docs[0].metadata["document_id"], "alex_chen")

    def test_08_pdf_source_override_applied_correctly(self):
        """Test source_override properly overrides the default filepath in metadata."""
        custom_src = "candidate_resume_uploaded.pdf"
        docs = self.pipeline.load_pdf(
            file_path=self.resume_alex_path,
            document_type="resume",
            document_id="alex_chen",
            candidate_id="alex_chen",
            source_override=custom_src,
        )
        self.assertGreater(len(docs), 0)
        self.assertEqual(docs[0].metadata["source"], custom_src)

    def test_09_pdf_chunking_with_source_override(self):
        """Test load_and_chunk_pdf preserves source_override across all chunks."""
        custom_src = "jd_backend_final.pdf"
        chunks = self.pipeline.load_and_chunk_pdf(
            file_path=self.jd_path,
            document_type="job_description",
            document_id="jd_lead",
            source_override=custom_src,
        )
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertEqual(chunk.metadata["source"], custom_src)
            self.assertEqual(chunk.metadata["document_type"], "job_description")
            self.assertIn("chunk_index", chunk.metadata)

    def test_10_actual_ingest_document_with_real_pdf_path(self):
        """Test AutomaticMatchService.ingest_document with a real PDF file path."""
        count = self.service.ingest_document(
            file_path_or_bytes=self.resume_alex_path,
            document_type="resume",
            document_id="alex_chen",
            candidate_id="alex_chen",
            filename="resume_alex_chen.pdf",
        )
        self.assertGreater(count, 0)

        # Verify indexed in Chroma
        res = self.retriever.search_resumes("Python", candidate_id="alex_chen")
        self.assertGreater(len(res), 0)

    def test_11_actual_ingest_document_with_real_pdf_bytes(self):
        """Test AutomaticMatchService.ingest_document with real PDF raw bytes (UI upload simulation)."""
        pdf_bytes = self.resume_priya_path.read_bytes()
        count = self.service.ingest_document(
            file_path_or_bytes=pdf_bytes,
            document_type="resume",
            document_id="priya_sharma",
            candidate_id="priya_sharma",
            filename="priya_resume_upload.pdf",
            replace=True,
        )
        self.assertGreater(count, 0)

        res = self.retriever.search_resumes("Microservices", candidate_id="priya_sharma")
        self.assertGreater(len(res), 0)
        self.assertEqual(res[0].metadata["source"], "priya_resume_upload.pdf")

    # --------------------------------------------------------------------------
    # 4. Automatic Workflow & PARITY Tests
    # --------------------------------------------------------------------------

    def test_12_automatic_match_triggered_by_real_pdf_ingestion(self):
        """Test real PDF resume + real PDF JD triggers automatic deterministic matching."""
        # 1. Ingest Resume
        c_resume = self.service.ingest_document(
            file_path_or_bytes=self.resume_alex_path,
            document_type="resume",
            document_id="alex_chen",
            candidate_id="alex_chen",
        )
        self.assertGreater(c_resume, 0)

        # Check readiness before JD
        r1 = self.service.run_automatic_match("alex_chen", "jd_senior_backend_lead")
        self.assertEqual(r1.status, "waiting_for_job_description")
        self.assertFalse(r1.documents_ready)

        # 2. Ingest JD
        c_jd = self.service.ingest_document(
            file_path_or_bytes=self.jd_path,
            document_type="job_description",
            document_id="jd_senior_backend_lead",
            job_id="jd_senior_backend_lead",
        )
        self.assertGreater(c_jd, 0)

        # 3. Check readiness and automatic match
        r2: AutomaticMatchResult = self.service.run_automatic_match("alex_chen", "jd_senior_backend_lead")
        self.assertEqual(r2.status, "match_ready")
        self.assertTrue(r2.documents_ready)
        self.assertIsNotNone(r2.match_result)
        self.assertIsNotNone(r2.summary_markdown)

    def test_13_automatic_match_result_equals_direct_m3_run_match(self):
        """Test parity: AutomaticMatchResult.match_result == direct run_match()."""
        self.service.ingest_document(
            file_path_or_bytes=self.resume_alex_path,
            document_type="resume",
            document_id="alex_chen",
            candidate_id="alex_chen",
        )
        self.service.ingest_document(
            file_path_or_bytes=self.jd_path,
            document_type="job_description",
            document_id="jd_senior_backend_lead",
            job_id="jd_senior_backend_lead",
        )

        auto_res = self.service.run_automatic_match("alex_chen", "jd_senior_backend_lead")
        direct_res = run_match(
            candidate_id="alex_chen",
            job_id="jd_senior_backend_lead",
            retriever=self.retriever,
            vectorstore_manager=self.vectorstore_manager,
        )

        self.assertEqual(auto_res.match_result.matched_skills, direct_res.matched_skills)
        self.assertEqual(auto_res.match_result.missing_skills, direct_res.missing_skills)
        self.assertEqual(auto_res.match_result.status, direct_res.status)

    def test_14_replacement_through_real_ingest_document(self):
        """Test ingest_document(..., replace=True) replaces prior chunks without chunk mixing."""
        # Initial ingest with alex
        self.service.ingest_document(
            file_path_or_bytes=self.resume_alex_path,
            document_type="resume",
            document_id="target_candidate",
            candidate_id="target_candidate",
            filename="v1.pdf",
            replace=True,
        )
        docs_v1 = self.retriever.search_resumes("Python", candidate_id="target_candidate", top_k=50)
        self.assertTrue(all(d.metadata["source"] == "v1.pdf" for d in docs_v1))

        # Re-ingest with Priya's resume as replacement
        self.service.ingest_document(
            file_path_or_bytes=self.resume_priya_path,
            document_type="resume",
            document_id="target_candidate",
            candidate_id="target_candidate",
            filename="v2.pdf",
            replace=True,
        )
        docs_v2 = self.retriever.search_resumes("Python", candidate_id="target_candidate", top_k=50)
        self.assertTrue(all(d.metadata["source"] == "v2.pdf" for d in docs_v2))
        self.assertFalse(any(d.metadata["source"] == "v1.pdf" for d in docs_v2))

    def test_15_candidate_isolation_with_real_ingestion(self):
        """Test candidate isolation: Alex and Priya chunks are never cross-pollinated."""
        self.service.ingest_document(
            file_path_or_bytes=self.resume_alex_path,
            document_type="resume",
            document_id="alex_chen",
            candidate_id="alex_chen",
        )
        self.service.ingest_document(
            file_path_or_bytes=self.resume_priya_path,
            document_type="resume",
            document_id="priya_sharma",
            candidate_id="priya_sharma",
        )

        alex_docs = self.retriever.search_resumes("Python", candidate_id="alex_chen", top_k=50)
        priya_docs = self.retriever.search_resumes("Python", candidate_id="priya_sharma", top_k=50)

        self.assertTrue(all(d.metadata["candidate_id"] == "alex_chen" for d in alex_docs))
        self.assertTrue(all(d.metadata["candidate_id"] == "priya_sharma" for d in priya_docs))

    # --------------------------------------------------------------------------
    # 5. Configuration & Manifests Tests
    # --------------------------------------------------------------------------

    def test_16_declared_dependencies_in_requirements_txt(self):
        """Test that requirements.txt declares streamlit, langchain-chroma, langchain-text-splitters."""
        req_content = Path("requirements.txt").read_text(encoding="utf-8")
        self.assertIn("streamlit", req_content)
        self.assertIn("langchain-chroma", req_content)
        self.assertIn("langchain-text-splitters", req_content)

    def test_17_declared_dependencies_in_pyproject_toml(self):
        """Test that pyproject.toml declares streamlit, langchain-chroma, langchain-text-splitters."""
        toml_content = Path("pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("streamlit", toml_content)
        self.assertIn("langchain-chroma", toml_content)
        self.assertIn("langchain-text-splitters", toml_content)

    def test_18_infra_manifests_use_qwen3_8b(self):
        """Test docker-compose and k8s configmap declare OLLAMA_MODEL=qwen3:8b."""
        dc_content = Path("infra/docker/docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("OLLAMA_MODEL=qwen3:8b", dc_content)
        self.assertNotIn("llama3:8b", dc_content)

        k8s_content = Path("infra/k8s/base/configmap.yaml").read_text(encoding="utf-8")
        self.assertIn('OLLAMA_MODEL: "qwen3:8b"', k8s_content)
        self.assertNotIn("llama3:8b", k8s_content)

    # --------------------------------------------------------------------------
    # 6. Documentation Consistency Tests
    # --------------------------------------------------------------------------

    def test_19_system_contract_reflects_deterministic_matching(self):
        """Test that SYSTEM_CONTRACT.md reflects pure set-based matching and no legacy scoring."""
        sc_content = Path("SYSTEM_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn(r"\text{matched} = \text{required} \cap \text{candidate}", sc_content)
        self.assertIn(r"\text{missing} = \text{required} \setminus \text{candidate}", sc_content)
        self.assertNotIn(r"Score = w_{skills}", sc_content)
        self.assertIn("Hallucination Ban", sc_content)


if __name__ == "__main__":
    unittest.main()
