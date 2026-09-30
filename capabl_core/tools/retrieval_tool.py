"""
Knowledge Retrieval Tool for the Recruitment Intelligence Agent.

CAPABL Requirement:
- LangChain @tool wrapping the metadata-aware retriever.
- Retrieves evidence strictly from Chroma persistent knowledge base.
- Preserves document isolation across 'resume', 'job_description', and 'policy'.
- Returns structured, useful evidence payloads.
"""

from typing import Literal, Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool, BaseTool

from capabl_core.rag.retriever import RecruitmentRetriever


class RetrievalQueryInput(BaseModel):
    """Input schema for the knowledge retrieval tool."""
    query: str = Field(
        ...,
        description="Factual semantic search query to look up in the verified knowledge base.",
    )
    document_type: Literal["resume", "job_description", "policy"] = Field(
        ...,
        description="The document category to search. Must strictly be 'resume', 'job_description', or 'policy'.",
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of evidence chunks to retrieve (1-10).",
    )
    candidate_id: Optional[str] = Field(
        default=None,
        description="Optional candidate ID to isolate retrieval to a specific candidate's resume.",
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Optional job ID to isolate retrieval to a specific job description.",
    )


def _execute_retrieval(
    retriever: RecruitmentRetriever,
    query: str,
    document_type: str,
    top_k: int = 4,
    candidate_id: Optional[str] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper executing retrieval and formatting structured evidence output."""
    try:
        additional_filters: Optional[Dict[str, Any]] = None
        if document_type == "resume" and candidate_id:
            additional_filters = {"candidate_id": candidate_id}
        elif document_type == "job_description" and job_id:
            additional_filters = {"document_id": job_id}

        docs = retriever.retrieve_by_type(
            query=query,
            document_type=document_type,
            top_k=top_k,
            additional_filters=additional_filters,
        )

        if not docs:
            return {
                "status": "no_evidence",
                "document_type": document_type,
                "count": 0,
                "results": [],
                "message": f"No evidence found in '{document_type}' documents matching query: '{query}'.",
            }

        formatted_results: List[Dict[str, Any]] = []
        for doc in docs:
            doc_cand = doc.metadata.get("candidate_id")
            if document_type == "resume" and candidate_id and doc_cand and doc_cand.strip().lower() != candidate_id.strip().lower():
                continue
            doc_job = doc.metadata.get("document_id")
            if document_type == "job_description" and job_id and doc_job and doc_job.strip().lower() != job_id.strip().lower():
                continue
            formatted_results.append(
                {
                    "content": doc.page_content.strip(),
                    "source": doc.metadata.get("source", "unknown"),
                    "page": doc.metadata.get("page", 0),
                    "document_id": doc.metadata.get("document_id", "unknown"),
                    "candidate_id": doc.metadata.get("candidate_id"),
                }
            )

        return {
            "status": "success",
            "document_type": document_type,
            "count": len(formatted_results),
            "results": formatted_results,
        }
    except Exception as exc:
        return {
            "status": "error",
            "document_type": document_type,
            "count": 0,
            "results": [],
            "message": f"Retrieval failed: {str(exc)}",
        }


def create_retrieval_tool(
    retriever: Optional[RecruitmentRetriever] = None,
) -> BaseTool:
    """
    Factory creating a LangChain BaseTool bound to a RecruitmentRetriever instance.
    Enables dependency injection for testing and isolated vector stores.
    """
    _lazy_retriever: Optional[RecruitmentRetriever] = retriever

    @tool(args_schema=RetrievalQueryInput)
    def retrieve_evidence(
        query: str,
        document_type: Literal["resume", "job_description", "policy"],
        top_k: int = 4,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve verified factual evidence from indexed documents in Chroma vector store.
        Use this tool whenever you need facts about candidate skills, experience,
        job requirements, or company HR policies.
        Enforces strict document type isolation.
        """
        nonlocal _lazy_retriever
        if _lazy_retriever is None:
            _lazy_retriever = RecruitmentRetriever()

        return _execute_retrieval(
            retriever=_lazy_retriever,
            query=query,
            document_type=document_type,
            top_k=top_k,
            candidate_id=candidate_id,
            job_id=job_id,
        )

    return retrieve_evidence


# Default tool instance pointing to standard persistent Chroma store
retrieve_evidence = create_retrieval_tool()
