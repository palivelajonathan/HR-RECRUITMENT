"""
Job Description Evidence Retrieval Tool for CAPABL Track 6 (Milestone 6).

LangChain @tool retrieving role requirements, mandatory qualifications, and responsibilities
strictly from document_type='job_description' with mandatory job_id scoping.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool, BaseTool

from capabl_core.evidence.service import EvidenceService


class JobEvidenceInput(BaseModel):
    """Input contract for job description evidence retrieval."""
    job_id: str = Field(
        ...,
        description="Unique identifier of the target job description (e.g. 'jd_senior_backend_lead', 'jd_backend_lead_2026').",
    )
    query: str = Field(
        ...,
        description="Factual semantic search query regarding job requirements, qualifications, responsibilities, or stack.",
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of job description excerpts to retrieve (1-10).",
    )


def create_job_evidence_tool(
    evidence_service: Optional[EvidenceService] = None,
) -> BaseTool:
    """
    Factory creating a LangChain BaseTool bound to an EvidenceService instance.
    Enables dependency injection for hermetic testing.
    """
    _service: Optional[EvidenceService] = evidence_service

    @tool("retrieve_job_evidence", args_schema=JobEvidenceInput)
    def retrieve_job_evidence(
        job_id: str,
        query: str,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """
        Retrieve verified factual requirements from an indexed Job Description.
        Use this tool whenever you need facts about mandatory qualifications,
        preferred skills, years of experience required, or day-to-day responsibilities.
        Strictly constrains retrieval to the specified job_id and prevents cross-job contamination.
        Never use this tool to search company HR policies or candidate resumes.
        """
        nonlocal _service
        if _service is None:
            _service = EvidenceService()

        envelope = _service.get_job_evidence(
            query=query,
            job_id=job_id,
            top_k=top_k,
        )
        return envelope.to_tool_dict()

    return retrieve_job_evidence


# Default instance bound to persistent Chroma store
retrieve_job_evidence = create_job_evidence_tool()
