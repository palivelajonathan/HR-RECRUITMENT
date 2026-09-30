"""
Evidence Domain Models for Milestone 6: Policy & Evidence Layer.

Defines standardized Pydantic v2 schemas for evidence extraction,
document isolation, and source-grounded answers.
"""

from enum import Enum
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PolicyCategory(str, Enum):
    """Common corporate HR and recruitment policy domains."""
    LEAVE_AND_ATTENDANCE = "leave_and_attendance"
    REMOTE_WORK = "remote_work"
    BENEFITS_AND_COMPENSATION = "benefits_and_compensation"
    CODE_OF_CONDUCT = "code_of_conduct"
    HIRING_GUIDELINES = "hiring_guidelines"
    GENERAL = "general"


class EvidenceItem(BaseModel):
    """
    Atomic unit of verified evidence retrieved from indexed Chroma documents.
    Preserves strict document boundary metadata, source provenance, and page citation.
    """
    document_type: Literal["resume", "job_description", "policy"] = Field(
        ...,
        description="The strict category of the source document.",
    )
    document_id: str = Field(
        ...,
        description="Unique identifier of the source document.",
    )
    source: str = Field(
        ...,
        description="File path or URI of the underlying PDF document.",
    )
    page: Optional[int] = Field(
        default=None,
        description="Zero-indexed or 1-indexed page number where the excerpt appears.",
    )
    excerpt: str = Field(
        ...,
        description="Verbatim or chunk text extracted from the document.",
    )
    candidate_id: Optional[str] = Field(
        default=None,
        description="Associated candidate ID if document_type is 'resume'.",
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Associated job ID if document_type is 'job_description'.",
    )
    policy_category: Optional[str] = Field(
        default=None,
        description="Associated policy category if document_type is 'policy'.",
    )


class EvidenceEnvelope(BaseModel):
    """
    Standardized response envelope returned by evidence retrieval tools and service layer.
    """
    status: Literal["success", "no_evidence", "error"] = Field(
        ...,
        description="Outcome of the evidence query.",
    )
    document_type: Literal["resume", "job_description", "policy"] = Field(
        ...,
        description="The document type targeted by the query.",
    )
    query: str = Field(
        ...,
        description="The search query used for retrieval.",
    )
    count: int = Field(
        default=0,
        description="Number of evidence items returned.",
    )
    items: List[EvidenceItem] = Field(
        default_factory=list,
        description="List of verified evidence items.",
    )
    message: str = Field(
        default="",
        description="Human-readable status, guidance, or error message.",
    )

    def to_tool_dict(self) -> Dict[str, Any]:
        """Convert envelope to serializable dictionary for LangChain tool output."""
        return {
            "status": self.status,
            "document_type": self.document_type,
            "query": self.query,
            "count": self.count,
            "results": [item.model_dump() for item in self.items],
            "message": self.message,
        }
