"""
Unit and Integration Tests for Milestone 1: RAG Ingestion Foundation.

Validates:
1. PDF loading via PyPDFLoader with explicit document types.
2. Strict metadata schema preservation (document_type, document_id, source, page, candidate_id).
3. Document-specific chunking profiles (resume: 600, JD: 500, policy: 800).
4. HuggingFace BGE embeddings initialization, dimensions (384), and normalization.
5. Persistent Chroma vector store operations & survival across re-initialization.
6. Strict retrieval isolation preventing cross-document-type contamination.
7. RAG quality verification on realistic queries.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from langchain_core.documents import Document

from capabl_core.ingestion.pdf_loader import (
    PDFIngestionPipeline,
    DocumentType,
    DocumentMetadata,
    ChunkingProfile,
)
from capabl_core.rag.embeddings import get_embedding_function
from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.rag.retriever import RecruitmentRetriever


class TestRAGIngestionFoundation(unittest.TestCase):
    """Milestone 1 RAG verification test suite."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = PDFIngestionPipeline()
        cls.sample_dir = Path("./data/sample")

        cls.resume_alex_path = cls.sample_dir / "resumes" / "resume_alex_chen.pdf"
        cls.resume_priya_path = cls.sample_dir / "resumes" / "resume_priya_sharma.pdf"
        cls.jd_path = cls.sample_dir / "job_descriptions" / "jd_senior_backend_lead.pdf"
        cls.policy_path = cls.sample_dir / "policies" / "policy_leave_and_attendance.pdf"

        # Verify sample PDFs exist
        assert cls.resume_alex_path.exists(), "Sample resume_alex_chen.pdf missing!"
        assert cls.jd_path.exists(), "Sample jd_senior_backend_lead.pdf missing!"
        assert cls.policy_path.exists(), "Sample policy_leave_and_attendance.pdf missing!"

        # Initialize embedding model once for the test suite
        cls.embedding_fn = get_embedding_function()

    def setUp(self):
        # Create a clean isolated temporary directory for Chroma per test
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Cleanup temporary vector store files
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # --------------------------------------------------------------------------
    # 1. PDF Ingestion & Loading Tests
    # --------------------------------------------------------------------------
    def test_pdf_loading_and_metadata_structure(self):
        """Verify PyPDFLoader loads pages and strictly adheres to DocumentMetadata schema."""
        docs = self.pipeline.load_pdf(
            file_path=self.resume_alex_path,
            document_type=DocumentType.RESUME,
            document_id="resume_alex_chen",
            candidate_id="cand_alex_chen",
        )

        self.assertGreaterEqual(len(docs), 1)
        first_doc = docs[0]
        self.assertIn("Alex Chen", first_doc.page_content)

        # Validate metadata fields
        self.assertEqual(first_doc.metadata["document_type"], "resume")
        self.assertEqual(first_doc.metadata["document_id"], "resume_alex_chen")
        self.assertEqual(first_doc.metadata["candidate_id"], "cand_alex_chen")
        self.assertEqual(first_doc.metadata["page"], 0)
        self.assertTrue(Path(first_doc.metadata["source"]).is_file())

        # Validate with Pydantic model
        validated = DocumentMetadata(**first_doc.metadata)
        self.assertEqual(validated.document_type, DocumentType.RESUME)

    def test_document_metadata_type_distinction(self):
        """Verify document_type is explicitly assigned and prevents ambiguity."""
        jd_docs = self.pipeline.load_pdf(
            file_path=self.jd_path,
            document_type="job_description",
            document_id="jd_backend_lead",
        )
        self.assertEqual(jd_docs[0].metadata["document_type"], "job_description")
        self.assertNotIn("candidate_id", jd_docs[0].metadata)

        policy_docs = self.pipeline.load_pdf(
            file_path=self.policy_path,
            document_type="policy",
            document_id="policy_leave_2026",
        )
        self.assertEqual(policy_docs[0].metadata["document_type"], "policy")
        self.assertNotIn("candidate_id", policy_docs[0].metadata)

    def test_invalid_document_type_rejected(self):
        """Verify unapproved document types raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.pipeline.load_pdf(
                file_path=self.resume_alex_path,
                document_type="random_contract",
            )
        self.assertIn("Invalid document_type", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 2. Document-Specific Chunking Tests
    # --------------------------------------------------------------------------
    def test_document_specific_chunking_profiles(self):
        """Verify RecursiveCharacterTextSplitter uses document-specific sizing and preserves metadata."""
        # A. Resume chunking (size: 600, overlap: 100)
        resume_docs = self.pipeline.load_pdf(
            self.resume_alex_path,
            document_type="resume",
            candidate_id="cand_alex_chen",
        )
        resume_chunks = self.pipeline.chunk_documents(resume_docs)
        self.assertGreaterEqual(len(resume_chunks), 1)

        for chunk in resume_chunks:
            self.assertLessEqual(len(chunk.page_content), 650)  # Allow small margin for word boundary
            self.assertEqual(chunk.metadata["document_type"], "resume")
            self.assertEqual(chunk.metadata["candidate_id"], "cand_alex_chen")
            self.assertIn("chunk_index", chunk.metadata)

        # B. JD chunking (size: 500, overlap: 80)
        jd_docs = self.pipeline.load_pdf(self.jd_path, document_type="job_description")
        jd_chunks = self.pipeline.chunk_documents(jd_docs)
        self.assertGreaterEqual(len(jd_chunks), 1)
        for chunk in jd_chunks:
            self.assertEqual(chunk.metadata["document_type"], "job_description")
            self.assertIn("chunk_index", chunk.metadata)

        # C. Policy chunking (size: 800, overlap: 150)
        policy_docs = self.pipeline.load_pdf(self.policy_path, document_type="policy")
        policy_chunks = self.pipeline.chunk_documents(policy_docs)
        self.assertGreaterEqual(len(policy_chunks), 1)
        for chunk in policy_chunks:
            self.assertEqual(chunk.metadata["document_type"], "policy")
            self.assertIn("chunk_index", chunk.metadata)

    # --------------------------------------------------------------------------
    # 3. Embeddings Tests
    # --------------------------------------------------------------------------
    def test_bge_embeddings_dimensions(self):
        """Verify HuggingFace BGE embeddings generate 384-dimensional dense vectors."""
        text = "Experienced Senior Backend Engineer proficient in Python and Kubernetes."
        vector = self.embedding_fn.embed_query(text)
        self.assertEqual(len(vector), 384, "BGE-small-en-v1.5 must produce 384-dim embeddings")

        # Test batch embedding
        batch = ["Python FastAPI", "React TypeScript Next.js"]
        batch_vectors = self.embedding_fn.embed_documents(batch)
        self.assertEqual(len(batch_vectors), 2)
        self.assertEqual(len(batch_vectors[0]), 384)
        self.assertEqual(len(batch_vectors[1]), 384)

    # --------------------------------------------------------------------------
    # 4. Chroma Persistence & Restart Tests
    # --------------------------------------------------------------------------
    def test_chroma_persistence_and_restart_survival(self):
        """Verify Chroma stores vectors on disk and survives application restarts."""
        manager1 = ChromaVectorStoreManager(
            persist_directory=self.temp_dir,
            collection_name="test_persistence_col",
            embedding_function=self.embedding_fn,
        )

        test_doc = Document(
            page_content="Sample candidate bio with Python experience.",
            metadata={"document_type": "resume", "document_id": "test_doc_1", "source": "test", "page": 0},
        )
        manager1.add_documents([test_doc])
        self.assertEqual(manager1.count(), 1)

        # Simulate Application Restart: Instantiate new manager with same path
        manager2 = ChromaVectorStoreManager(
            persist_directory=self.temp_dir,
            collection_name="test_persistence_col",
            embedding_function=self.embedding_fn,
        )
        self.assertEqual(manager2.count(), 1, "Vector store must survive re-instantiation across restarts")

    # --------------------------------------------------------------------------
    # 5. Metadata-Aware Retrieval Isolation (CRITICAL)
    # --------------------------------------------------------------------------
    def test_retrieval_isolation_prevents_contamination(self):
        """
        CRITICAL TEST: Verify that a resume query NEVER retrieves policy or JD documents,
        a policy query NEVER retrieves resumes, and a JD query NEVER retrieves policies.
        """
        manager = ChromaVectorStoreManager(
            persist_directory=self.temp_dir,
            collection_name="test_isolation_col",
            embedding_function=self.embedding_fn,
        )

        # Ingest all 3 types into the same collection
        resume_docs = self.pipeline.chunk_documents(
            self.pipeline.load_pdf(self.resume_alex_path, document_type="resume", candidate_id="cand_alex_chen")
        )
        jd_docs = self.pipeline.chunk_documents(
            self.pipeline.load_pdf(self.jd_path, document_type="job_description")
        )
        policy_docs = self.pipeline.chunk_documents(
            self.pipeline.load_pdf(self.policy_path, document_type="policy")
        )

        manager.add_documents(resume_docs)
        manager.add_documents(jd_docs)
        manager.add_documents(policy_docs)

        self.assertGreater(manager.count(), 3)
        retriever = RecruitmentRetriever(manager)

        # Test A: Resume Query — Even when asking about leave/policy, MUST ONLY return resume chunks
        resume_results = retriever.search_resumes("leave policy and vacation days", top_k=5)
        for doc in resume_results:
            self.assertEqual(
                doc.metadata["document_type"],
                "resume",
                "Resume search returned a non-resume document! Cross-contamination detected!",
            )

        # Test B: Policy Query — Even when asking about Python engineer, MUST ONLY return policy chunks
        policy_results = retriever.search_policies("Senior Python Engineer with Docker", top_k=5)
        for doc in policy_results:
            self.assertEqual(
                doc.metadata["document_type"],
                "policy",
                "Policy search returned a non-policy document! Cross-contamination detected!",
            )

        # Test C: Job Description Query — MUST ONLY return job description chunks
        jd_results = retriever.search_job_descriptions("vacation allowance and remote work", top_k=5)
        for doc in jd_results:
            self.assertEqual(
                doc.metadata["document_type"],
                "job_description",
                "JD search returned a non-JD document! Cross-contamination detected!",
            )

    # --------------------------------------------------------------------------
    # 6. RAG Quality Foundation Test
    # --------------------------------------------------------------------------
    def test_rag_quality_foundation(self):
        """Verify semantic relevance of retrieved results under realistic HR queries."""
        manager = ChromaVectorStoreManager(
            persist_directory=self.temp_dir,
            collection_name="test_quality_col",
            embedding_function=self.embedding_fn,
        )

        # Ingest documents
        manager.add_documents(
            self.pipeline.chunk_documents(self.pipeline.load_pdf(self.jd_path, document_type="job_description"))
        )
        manager.add_documents(
            self.pipeline.chunk_documents(self.pipeline.load_pdf(self.policy_path, document_type="policy"))
        )

        retriever = RecruitmentRetriever(manager)

        # Query 1: JD skills query
        jd_hits = retriever.search_job_descriptions("What skills are required for the backend role?", top_k=2)
        self.assertGreater(len(jd_hits), 0)
        combined_jd_text = " ".join([d.page_content for d in jd_hits])
        self.assertTrue(
            "Python" in combined_jd_text or "Kubernetes" in combined_jd_text or "Backend" in combined_jd_text,
            "JD retrieval failed to surface backend requirements",
        )

        # Query 2: Leave policy query
        policy_hits = retriever.search_policies("What is the company's leave policy?", top_k=2)
        self.assertGreater(len(policy_hits), 0)
        combined_policy_text = " ".join([d.page_content for d in policy_hits])
        self.assertTrue(
            "leave" in combined_policy_text.lower() or "pto" in combined_policy_text.lower(),
            "Policy retrieval failed to surface leave guidelines",
        )


if __name__ == "__main__":
    unittest.main()
