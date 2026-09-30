"""
Automatic Resume + JD Match Workflow Service.

CAPABL Track 6 Requirement:
- Connects document upload and indexing state to the existing deterministic M3 match engine.
- Reuses run_match(candidate_id, job_id) without duplicating matching logic.
- Triggers automatic matching ONLY when both resume and JD are available.
- Handles document replacement with targeted chunk deletion (zero global wipe).
- Preserves cross-candidate and cross-job document isolation.
- Returns structured AutomaticMatchResult with proactive factual summary.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from langchain_core.documents import Document

from capabl_core.matching.models import MatchResult
from capabl_core.matching.matcher import run_match, _fetch_documents_from_store
from capabl_core.ingestion.pdf_loader import PDFIngestionPipeline
from capabl_core.ingestion.validator import validate_pdf_content
from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.rag.retriever import RecruitmentRetriever
from capabl_core.workflow.models import (
    WorkflowStatus,
    WorkflowContext,
    AutomaticMatchResult,
    format_match_summary_markdown,
)

logger = logging.getLogger(__name__)


class AutomaticMatchService:
    """
    Coordinates document ingestion, readiness tracking, and automatic execution
    of the deterministic Resume-to-JD match engine.
    """

    def __init__(
        self,
        vectorstore_manager: Optional[ChromaVectorStoreManager] = None,
        retriever: Optional[RecruitmentRetriever] = None,
        ingestion_pipeline: Optional[PDFIngestionPipeline] = None,
    ):
        self.vectorstore_manager = vectorstore_manager or ChromaVectorStoreManager()
        self.retriever = retriever or RecruitmentRetriever(vectorstore_or_manager=self.vectorstore_manager)
        self.ingestion_pipeline = ingestion_pipeline or PDFIngestionPipeline()

    def ingest_document(
        self,
        file_path_or_bytes: Union[str, bytes, Path],
        document_type: str,
        document_id: str,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        filename: Optional[str] = None,
        replace: bool = True,
    ) -> int:
        """
        Ingests and indexes a resume, job description, or policy document into Chroma.
        Supports document replacement by purging prior chunks for that specific document.
        
        Args:
            file_path_or_bytes: Local file path or raw bytes of the PDF.
            document_type: Must be 'resume', 'job_description', or 'policy'.
            document_id: Unique document identifier.
            candidate_id: Candidate identifier (required for resumes).
            job_id: Job identifier (required for JDs).
            filename: Source display filename.
            replace: If True, deletes prior indexed chunks for this document before indexing.
            
        Returns:
            int: Number of chunks indexed into Chroma.
        """
        clean_doc_type = document_type.strip().lower()
        if clean_doc_type not in ("resume", "job_description", "policy"):
            raise ValueError(
                f"Invalid document_type '{document_type}'. Must be 'resume', 'job_description', or 'policy'."
            )

        clean_doc_id = document_id.strip()
        cid = candidate_id.strip().lower() if candidate_id else None
        jid = job_id.strip().lower() if job_id else None

        # Targeted deletion on replacement (defense against chunk mixing)
        if replace:
            self._delete_previous_chunks(
                document_type=clean_doc_type,
                document_id=clean_doc_id,
                candidate_id=cid,
                job_id=jid,
            )

        # Validate PDF content, sanitize filename, and enforce resource limits
        validated_bytes, clean_filename = validate_pdf_content(
            file_path_or_bytes=file_path_or_bytes,
            filename=filename,
        )

        # Handle raw bytes by writing to secure temporary file for PyPDFLoader
        temp_file_path: Optional[str] = None
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(validated_bytes)
            temp_file_path = tmp.name
        target_path = temp_file_path
        src_name = clean_filename

        try:
            chunks = self.ingestion_pipeline.load_and_chunk_pdf(
                file_path=target_path,
                document_type=clean_doc_type,
                document_id=clean_doc_id,
                candidate_id=cid,
                source_override=src_name,
            )
            if chunks:
                # Enforce chunk ceiling if configured
                try:
                    from capabl_core.config.settings import get_settings
                    max_chunks = get_settings().max_document_chunks
                    if len(chunks) > max_chunks:
                        logger.warning(
                            f"Document '{clean_doc_id}' exceeded chunk ceiling "
                            f"({len(chunks)} > {max_chunks}). Truncating to {max_chunks} chunks."
                        )
                        chunks = chunks[:max_chunks]
                except Exception:
                    pass

                # Add job_id to metadata if job_description
                if clean_doc_type == "job_description" and jid:
                    for chunk in chunks:
                        chunk.metadata["job_id"] = jid

                self.vectorstore_manager.index_documents(chunks)
                return len(chunks)
            return 0
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as exc:
                    logger.debug(f"Could not remove temp file {temp_file_path}: {exc}")

    def _delete_previous_chunks(
        self,
        document_type: str,
        document_id: str,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> int:
        """Deletes prior chunks matching document identity without global store wipe."""
        deleted_count = 0
        if document_type == "resume":
            if candidate_id:
                deleted_count += self.vectorstore_manager.delete_documents(
                    where={"$and": [{"document_type": "resume"}, {"candidate_id": candidate_id}]}
                )
            if document_id and document_id != candidate_id:
                deleted_count += self.vectorstore_manager.delete_documents(
                    where={"$and": [{"document_type": "resume"}, {"document_id": document_id}]}
                )
        elif document_type == "job_description":
            if job_id:
                deleted_count += self.vectorstore_manager.delete_documents(
                    where={"$and": [{"document_type": "job_description"}, {"job_id": job_id}]}
                )
            if document_id:
                deleted_count += self.vectorstore_manager.delete_documents(
                    where={"$and": [{"document_type": "job_description"}, {"document_id": document_id}]}
                )
        return deleted_count

    def check_readiness(self, candidate_id: str, job_id: str) -> WorkflowStatus:
        """
        Determines whether the workflow has both required documents available in Chroma.
        
        Args:
            candidate_id: Candidate identifier.
            job_id: Job description identifier.
            
        Returns:
            WorkflowStatus ('ready_for_match', 'waiting_for_resume', etc.)
        """
        if not candidate_id or not candidate_id.strip() or not job_id or not job_id.strip():
            return "invalid_workflow"

        store = self.vectorstore_manager.get_or_create_store()
        resume_docs = _fetch_documents_from_store(store, "resume", candidate_id.strip())
        jd_docs = _fetch_documents_from_store(store, "job_description", job_id.strip())

        has_resume = len(resume_docs) > 0
        has_jd = len(jd_docs) > 0

        if has_resume and has_jd:
            return "ready_for_match"
        elif has_resume and not has_jd:
            return "waiting_for_job_description"
        elif not has_resume and has_jd:
            return "waiting_for_resume"
        else:
            return "waiting_for_document"

    def run_automatic_match(
        self,
        candidate_id: str,
        job_id: str,
        trigger: str = "automatic",
    ) -> AutomaticMatchResult:
        """
        Executes the automatic match workflow for a given candidate and job description.
        
        Boundary:
        - Only runs deterministic M3 match if BOTH documents exist.
        - Emits structured AutomaticMatchResult.
        - Zero LLM dependency for matching.
        """
        clean_cid = candidate_id.strip() if candidate_id else ""
        clean_jid = job_id.strip() if job_id else ""

        if not clean_cid or not clean_jid:
            return AutomaticMatchResult(
                status="invalid_workflow",
                candidate_id=clean_cid or None,
                job_id=clean_jid or None,
                documents_ready=False,
                message="Both candidate_id and job_id are required to execute matching.",
            )

        # Check document readiness in vector store
        readiness_status = self.check_readiness(clean_cid, clean_jid)
        if readiness_status != "ready_for_match":
            msg_map = {
                "waiting_for_job_description": f"Resume for '{clean_cid}' is indexed. Waiting for Job Description '{clean_jid}' upload.",
                "waiting_for_resume": f"Job Description '{clean_jid}' is indexed. Waiting for Resume for '{clean_cid}' upload.",
                "waiting_for_document": f"Waiting for both candidate resume and job description to be uploaded.",
            }
            return AutomaticMatchResult(
                status=readiness_status,
                candidate_id=clean_cid,
                job_id=clean_jid,
                documents_ready=False,
                message=msg_map.get(readiness_status, f"Workflow waiting: {readiness_status}"),
            )

        # Both documents ready -> Execute deterministic M3 matching engine
        try:
            match_res: MatchResult = run_match(
                candidate_id=clean_cid,
                job_id=clean_jid,
                retriever=self.retriever,
                vectorstore_manager=self.vectorstore_manager,
            )

            if match_res.status == "insufficient_evidence":
                return AutomaticMatchResult(
                    status="waiting_for_document",
                    candidate_id=clean_cid,
                    job_id=clean_jid,
                    match_result=match_res,
                    documents_ready=False,
                    message=match_res.message,
                )

            summary_md = format_match_summary_markdown(match_res)

            return AutomaticMatchResult(
                status="match_ready",
                candidate_id=clean_cid,
                job_id=clean_jid,
                match_result=match_res,
                trigger=trigger,
                documents_ready=True,
                summary_markdown=summary_md,
                message="Automatic match calculation completed successfully.",
            )

        except Exception as exc:
            logger.error(f"Error during automatic match execution: {exc}", exc_info=True)
            return AutomaticMatchResult(
                status="match_error",
                candidate_id=clean_cid,
                job_id=clean_jid,
                documents_ready=True,
                message=f"Deterministic match engine error: {str(exc)}",
            )


# Global singleton instance for runtime and Streamlit application
DEFAULT_WORKFLOW_SERVICE = AutomaticMatchService()


def run_automatic_match(
    candidate_id: str,
    job_id: str,
    workflow_service: Optional[AutomaticMatchService] = None,
) -> AutomaticMatchResult:
    """Convenience functional API for automatic match execution."""
    service = workflow_service or DEFAULT_WORKFLOW_SERVICE
    return service.run_automatic_match(candidate_id=candidate_id, job_id=job_id)
