"""
Evidence Service for Milestone 6: Policy & Evidence Layer.

Provides clean facade over RecruitmentRetriever with strict cross-domain isolation,
per-candidate scoping, per-job scoping, and structured EvidenceEnvelope returns.
"""

import logging
from typing import Optional, List, Dict, Any, Union
from langchain_chroma import Chroma

from capabl_core.rag.retriever import RecruitmentRetriever
from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.ingestion.pdf_loader import DocumentType
from capabl_core.evidence.models import EvidenceItem, EvidenceEnvelope, PolicyCategory

logger = logging.getLogger(__name__)


class EvidenceService:
    """
    Evidence orchestration service enforcing document-type boundaries,
    entity-level isolation, and structured envelope serialization.
    """

    def __init__(
        self,
        retriever: Optional[RecruitmentRetriever] = None,
        vectorstore_or_manager: Optional[Union[Chroma, ChromaVectorStoreManager]] = None,
    ):
        if retriever is not None:
            self.retriever = retriever
        elif vectorstore_or_manager is not None:
            self.retriever = RecruitmentRetriever(vectorstore_or_manager=vectorstore_or_manager)
        else:
            self.retriever = RecruitmentRetriever()

    def get_policy_evidence(
        self,
        query: str,
        category: Optional[Union[PolicyCategory, str]] = None,
        top_k: int = 4,
    ) -> EvidenceEnvelope:
        """
        Retrieves evidence strictly from policy documents.
        Enforces that candidate data and JD data are NEVER returned.
        """
        try:
            category_str = category.value if isinstance(category, PolicyCategory) else category
            additional_filters: Optional[Dict[str, Any]] = None
            if category_str:
                additional_filters = {"policy_category": category_str}

            docs = self.retriever.search_policies(
                query=query,
                top_k=top_k,
                additional_filters=additional_filters,
            )

            # Fallback: if category filter yielded 0 hits, try search without category filter
            # and match category semantically in text
            if not docs and category_str:
                broad_docs = self.retriever.search_policies(query=f"{category_str} {query}", top_k=top_k)
                docs = broad_docs

            items: List[EvidenceItem] = []
            for doc in docs:
                actual_type = doc.metadata.get("document_type")
                if actual_type != "policy":
                    logger.error(
                        f"CRITICAL ISOLATION BREACH: Expected policy document, got {actual_type}. Dropping."
                    )
                    continue

                items.append(
                    EvidenceItem(
                        document_type="policy",
                        document_id=str(doc.metadata.get("document_id", "unknown")),
                        source=str(doc.metadata.get("source", "unknown")),
                        page=doc.metadata.get("page", 0),
                        excerpt=doc.page_content.strip(),
                        candidate_id=None,
                        job_id=None,
                        policy_category=doc.metadata.get("policy_category") or category_str,
                    )
                )

            if not items:
                return EvidenceEnvelope(
                    status="no_evidence",
                    document_type="policy",
                    query=query,
                    count=0,
                    items=[],
                    message=f"No corporate policy evidence found matching query: '{query}'.",
                )

            return EvidenceEnvelope(
                status="success",
                document_type="policy",
                query=query,
                count=len(items),
                items=items,
                message=f"Found {len(items)} policy evidence excerpt(s).",
            )

        except Exception as exc:
            logger.error(f"Error retrieving policy evidence: {exc}", exc_info=True)
            return EvidenceEnvelope(
                status="error",
                document_type="policy",
                query=query,
                count=0,
                items=[],
                message=f"Failed to retrieve policy evidence: {str(exc)}",
            )

    def get_candidate_evidence(
        self,
        query: str,
        candidate_id: str,
        top_k: int = 4,
    ) -> EvidenceEnvelope:
        """
        Retrieves evidence strictly from candidate resumes for the specified candidate_id.
        Cross-candidate contamination is strictly prevented.
        """
        clean_cand_id = (candidate_id or "").strip()
        if not clean_cand_id:
            return EvidenceEnvelope(
                status="no_evidence",
                document_type="resume",
                query=query,
                count=0,
                items=[],
                message="Cannot retrieve candidate evidence without a valid candidate_id.",
            )

        try:
            docs = self.retriever.search_resumes(
                query=query,
                top_k=top_k,
                candidate_id=clean_cand_id,
            )

            items: List[EvidenceItem] = []
            for doc in docs:
                actual_type = doc.metadata.get("document_type")
                actual_cand_id = doc.metadata.get("candidate_id")

                # STRICT DEFENSE-IN-DEPTH ISOLATION CHECK:
                if actual_type != "resume":
                    logger.error(
                        f"CRITICAL ISOLATION BREACH: Expected resume document, got {actual_type}. Dropping."
                    )
                    continue

                if actual_cand_id != clean_cand_id:
                    logger.error(
                        f"CRITICAL CROSS-CANDIDATE CONTAMINATION: Expected candidate '{clean_cand_id}', "
                        f"found '{actual_cand_id}'. Dropping chunk."
                    )
                    continue

                items.append(
                    EvidenceItem(
                        document_type="resume",
                        document_id=str(doc.metadata.get("document_id", "unknown")),
                        source=str(doc.metadata.get("source", "unknown")),
                        page=doc.metadata.get("page", 0),
                        excerpt=doc.page_content.strip(),
                        candidate_id=clean_cand_id,
                        job_id=None,
                        policy_category=None,
                    )
                )

            if not items:
                return EvidenceEnvelope(
                    status="no_evidence",
                    document_type="resume",
                    query=query,
                    count=0,
                    items=[],
                    message=f"No resume evidence found for candidate '{clean_cand_id}' matching query: '{query}'.",
                )

            return EvidenceEnvelope(
                status="success",
                document_type="resume",
                query=query,
                count=len(items),
                items=items,
                message=f"Found {len(items)} resume excerpt(s) for candidate '{clean_cand_id}'.",
            )

        except Exception as exc:
            logger.error(f"Error retrieving candidate evidence: {exc}", exc_info=True)
            return EvidenceEnvelope(
                status="error",
                document_type="resume",
                query=query,
                count=0,
                items=[],
                message=f"Failed to retrieve candidate evidence: {str(exc)}",
            )

    def get_job_evidence(
        self,
        query: str,
        job_id: str,
        top_k: int = 4,
    ) -> EvidenceEnvelope:
        """
        Retrieves evidence strictly from job descriptions for the specified job_id.
        Cross-job contamination is strictly prevented.
        """
        clean_job_id = (job_id or "").strip()
        if not clean_job_id:
            return EvidenceEnvelope(
                status="no_evidence",
                document_type="job_description",
                query=query,
                count=0,
                items=[],
                message="Cannot retrieve job evidence without a valid job_id.",
            )

        try:
            docs = self.retriever.search_job_descriptions(
                query=query,
                top_k=top_k,
                job_id=clean_job_id,
            )

            items: List[EvidenceItem] = []
            for doc in docs:
                actual_type = doc.metadata.get("document_type")
                actual_job_id = doc.metadata.get("document_id")

                # STRICT DEFENSE-IN-DEPTH ISOLATION CHECK:
                if actual_type != "job_description":
                    logger.error(
                        f"CRITICAL ISOLATION BREACH: Expected job_description document, got {actual_type}. Dropping."
                    )
                    continue

                if actual_job_id != clean_job_id:
                    logger.error(
                        f"CRITICAL CROSS-JOB CONTAMINATION: Expected job '{clean_job_id}', "
                        f"found '{actual_job_id}'. Dropping chunk."
                    )
                    continue

                items.append(
                    EvidenceItem(
                        document_type="job_description",
                        document_id=clean_job_id,
                        source=str(doc.metadata.get("source", "unknown")),
                        page=doc.metadata.get("page", 0),
                        excerpt=doc.page_content.strip(),
                        candidate_id=None,
                        job_id=clean_job_id,
                        policy_category=None,
                    )
                )

            if not items:
                return EvidenceEnvelope(
                    status="no_evidence",
                    document_type="job_description",
                    query=query,
                    count=0,
                    items=[],
                    message=f"No job description evidence found for job '{clean_job_id}' matching query: '{query}'.",
                )

            return EvidenceEnvelope(
                status="success",
                document_type="job_description",
                query=query,
                count=len(items),
                items=items,
                message=f"Found {len(items)} job description excerpt(s) for job '{clean_job_id}'.",
            )

        except Exception as exc:
            logger.error(f"Error retrieving job description evidence: {exc}", exc_info=True)
            return EvidenceEnvelope(
                status="error",
                document_type="job_description",
                query=query,
                count=0,
                items=[],
                message=f"Failed to retrieve job description evidence: {str(exc)}",
            )
