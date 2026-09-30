"""
Candidate Evidence Retrieval Tool for CAPABL Track 6 (Milestone 6).

LangChain @tool retrieving candidate skills, experience, and education
strictly from document_type='resume' with mandatory candidate_id scoping.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool, BaseTool

from capabl_core.evidence.service import EvidenceService


class CandidateEvidenceInput(BaseModel):
    """Input contract for candidate resume evidence retrieval."""
    candidate_id: str = Field(
        ...,
        description="Unique identifier of the target candidate (e.g. 'alex_chen', 'priya_sharma').",
    )
    query: str = Field(
        ...,
        description="Factual semantic search query regarding candidate qualifications, experience, or skills.",
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of resume excerpts to retrieve (1-10).",
    )


def create_candidate_evidence_tool(
    evidence_service: Optional[EvidenceService] = None,
) -> BaseTool:
    """
    Factory creating a LangChain BaseTool bound to an EvidenceService instance.
    Enables dependency injection for hermetic testing.
    """
    _service: Optional[EvidenceService] = evidence_service

    @tool("retrieve_candidate_evidence", args_schema=CandidateEvidenceInput)
    def retrieve_candidate_evidence(
        candidate_id: str,
        query: str,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """
        Retrieve verified factual evidence from an applicant's resume.
        Use this tool whenever you need facts about a candidate's background,
        employment history, education, or demonstrated technical skills.
        Strictly constrains retrieval to the specified candidate_id and prevents cross-candidate contamination.
        Never use this tool to search company HR policies.
        """
        nonlocal _service
        if _service is None:
            _service = EvidenceService()

        envelope = _service.get_candidate_evidence(
            query=query,
            candidate_id=candidate_id,
            top_k=top_k,
        )
        return envelope.to_tool_dict()

    return retrieve_candidate_evidence


# Default instance bound to persistent Chroma store
retrieve_candidate_evidence = create_candidate_evidence_tool()
