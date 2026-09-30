"""
Metadata-Aware Retrieval Subsystem.

CAPABL Requirement:
- Metadata-aware retrieval supporting:
  * Policy retrieval (document_type = 'policy')
  * Resume retrieval (document_type = 'resume')
  * Job Description retrieval (document_type = 'job_description')
- Strict cross-document-type contamination prevention:
  * A policy query MUST NOT retrieve a candidate's resume.
  * A resume query MUST NOT retrieve handbook content.
  * A JD query MUST NOT retrieve policy content.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from langchain_core.documents import Document
from langchain_chroma import Chroma

from capabl_core.ingestion.pdf_loader import DocumentType
from capabl_core.rag.vectorstore import ChromaVectorStoreManager

logger = logging.getLogger(__name__)


class RecruitmentRetriever:
    """Provides metadata-filtered semantic retrieval isolated by document category."""

    def __init__(
        self,
        vectorstore_or_manager: Optional[Union[Chroma, ChromaVectorStoreManager]] = None,
        vector_store_manager: Optional[Union[Chroma, ChromaVectorStoreManager]] = None,
    ):
        target = vectorstore_or_manager or vector_store_manager
        if target is None:
            manager = ChromaVectorStoreManager()
            self.vectorstore: Chroma = manager.get_or_create_store()
        elif isinstance(target, ChromaVectorStoreManager):
            self.vectorstore: Chroma = target.get_or_create_store()
        else:
            self.vectorstore: Chroma = target

    @staticmethod
    def _normalize_document_type(doc_type: Union[DocumentType, str]) -> str:
        if isinstance(doc_type, DocumentType):
            return doc_type.value
        clean = str(doc_type).strip().lower()
        valid_values = [t.value for t in DocumentType]
        if clean not in valid_values:
            raise ValueError(f"Invalid document_type '{doc_type}'. Allowed types are: {valid_values}")
        return clean

    def _build_filter(
        self,
        document_type: str,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Constructs Chroma-compatible metadata filter ensuring document_type isolation."""
        type_filter = {"document_type": document_type}

        if not additional_filters:
            return type_filter

        # Chroma supports $and operators for multiple criteria
        filter_list = [type_filter]
        for key, value in additional_filters.items():
            if value is not None:
                filter_list.append({key: value})

        if len(filter_list) == 1:
            return filter_list[0]
        return {"$and": filter_list}

    def retrieve_by_type(
        self,
        query: str,
        document_type: Union[DocumentType, str],
        top_k: int = 5,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Executes semantic similarity search strictly filtered by document_type.
        Enforces post-retrieval isolation guarantee.

        Args:
            query: Semantic search query string.
            document_type: 'resume', 'job_description', or 'policy'.
            top_k: Maximum number of chunks to return.
            additional_filters: Optional additional metadata key-value filters.

        Returns:
            List[Document]: Filtered documents matching the requested document_type only.
        """
        target_type = self._normalize_document_type(document_type)
        chroma_filter = self._build_filter(target_type, additional_filters)

        raw_results = self.vectorstore.similarity_search(
            query=query,
            k=top_k,
            filter=chroma_filter,
        )

        # STRICT ISOLATION POST-CHECK:
        # Guarantee zero cross-document-type contamination even under edge cases.
        isolated_results: List[Document] = []
        for doc in raw_results:
            actual_type = doc.metadata.get("document_type")
            if actual_type == target_type:
                isolated_results.append(doc)
            else:
                logger.error(
                    f"CRITICAL: Cross-contamination intercepted! Expected document_type '{target_type}', "
                    f"found '{actual_type}' in document_id '{doc.metadata.get('document_id')}'. "
                    f"Dropping chunk from results."
                )

        return isolated_results

    def search_resumes(
        self,
        query: str,
        top_k: int = 5,
        candidate_id: Optional[str] = None,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Retrieves candidate resume chunks only."""
        filters = dict(additional_filters or {})
        if candidate_id:
            filters["candidate_id"] = candidate_id
        return self.retrieve_by_type(
            query=query,
            document_type=DocumentType.RESUME,
            top_k=top_k,
            additional_filters=filters or None,
        )

    def search_job_descriptions(
        self,
        query: str,
        top_k: int = 5,
        job_id: Optional[str] = None,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Retrieves job description chunks only."""
        filters = dict(additional_filters or {})
        if job_id:
            filters["document_id"] = job_id
        return self.retrieve_by_type(
            query=query,
            document_type=DocumentType.JOB_DESCRIPTION,
            top_k=top_k,
            additional_filters=filters or None,
        )

    def search_policies(
        self,
        query: str,
        top_k: int = 5,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Retrieves company handbook and HR policy chunks only."""
        return self.retrieve_by_type(
            query=query,
            document_type=DocumentType.POLICY,
            top_k=top_k,
            additional_filters=additional_filters,
        )

    def retrieve_candidate_evidence(
        self,
        candidate_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[Document]:
        """Convenience alias retrieving candidate resume chunks."""
        return self.search_resumes(query=query, candidate_id=candidate_id, top_k=top_k)

    def retrieve_job_evidence(
        self,
        job_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[Document]:
        """Convenience alias retrieving job description chunks."""
        return self.search_job_descriptions(query=query, job_id=job_id, top_k=top_k)

    def retrieve_policy_evidence(
        self,
        query: str,
        policy_category: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Document]:
        """Convenience alias retrieving company policy chunks."""
        filters = {"policy_category": policy_category} if policy_category else None
        docs = self.search_policies(query=query, top_k=top_k, additional_filters=filters)
        if not docs and policy_category:
            docs = self.search_policies(query=f"{policy_category} {query}", top_k=top_k)
        return docs
