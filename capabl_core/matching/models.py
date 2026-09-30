"""
Pydantic Data Models for Deterministic Resume-to-JD Match Engine.

CAPABL Track 6 Requirement:
- Deterministic, verifiable matching data contracts.
- Factual representations of matched skills, missing skills, and evidence citations.
- Zero subjective scores, qualification percentages, or LLM-invented tiers.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class SkillEvidence(BaseModel):
    """Verifiable source evidence linking a skill to a specific document location."""
    skill: str = Field(..., description="Normalized canonical skill name")
    source: str = Field(..., description="Source file path or URI where skill was identified")
    page: Optional[int] = Field(default=None, description="0-indexed page number within source document")
    document_id: Optional[str] = Field(default=None, description="Document identifier")
    excerpt: str = Field(..., description="Exact textual excerpt or sentence containing the skill mention")


class MatchResult(BaseModel):
    """Deterministic match result contract between a candidate profile and job description."""
    candidate_id: str = Field(..., description="Identifier of candidate or resume document")
    job_id: str = Field(..., description="Identifier of job description or document")
    matched_skills: List[str] = Field(
        default_factory=list,
        description="Canonical skills present in both JD requirements and candidate resume",
    )
    missing_skills: List[str] = Field(
        default_factory=list,
        description="Canonical skills required by JD but missing in candidate resume",
    )
    matched_evidence: List[SkillEvidence] = Field(
        default_factory=list,
        description="Verifiable source citations from candidate resume for each matched skill",
    )
    candidate_skills: List[str] = Field(
        default_factory=list,
        description="All canonical skills identified in the candidate resume",
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="All canonical skills identified as required in the job description",
    )
    status: Literal["complete", "insufficient_evidence", "error"] = Field(
        default="complete",
        description="Status of the match evaluation",
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional diagnostic or status message",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable dictionary representation."""
        return self.model_dump()
