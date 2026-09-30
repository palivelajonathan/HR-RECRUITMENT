"""
Domain models for the Automatic Resume + JD Match Workflow.

CAPABL Track 6 Requirement:
- Proactive workflow execution upon availability of both Resume and Job Description.
- Explicit workflow states (waiting_for_resume, waiting_for_job_description, match_ready, etc.).
- Structured AutomaticMatchResult embedding the deterministic MatchResult.
- Zero subjective scores, arbitrary percentages, or hiring/rejection recommendations.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

from capabl_core.matching.models import MatchResult


WorkflowStatus = Literal[
    "waiting_for_document",
    "waiting_for_resume",
    "waiting_for_job_description",
    "ready_for_match",
    "matching",
    "match_ready",
    "invalid_workflow",
    "ingestion_error",
    "match_error",
]


class WorkflowContext(BaseModel):
    """Encapsulates the state and identity context for a candidate-job pair."""
    candidate_id: str = Field(..., description="Unique candidate identifier")
    job_id: str = Field(..., description="Unique job description identifier")
    resume_uploaded: bool = Field(default=False, description="Whether resume document is indexed")
    job_uploaded: bool = Field(default=False, description="Whether JD document is indexed")
    resume_source: Optional[str] = Field(default=None, description="Source path of indexed resume")
    job_source: Optional[str] = Field(default=None, description="Source path of indexed JD")
    resume_chunk_count: int = Field(default=0, description="Total chunks indexed for resume")
    job_chunk_count: int = Field(default=0, description="Total chunks indexed for JD")
    status: WorkflowStatus = Field(default="waiting_for_document", description="Current workflow state")
    message: Optional[str] = Field(default=None, description="Status or diagnostic explanation")


class AutomaticMatchResult(BaseModel):
    """Structured contract emitted by the automatic match workflow."""
    status: WorkflowStatus = Field(..., description="Current status of the match workflow")
    candidate_id: Optional[str] = Field(default=None, description="Target candidate identifier")
    job_id: Optional[str] = Field(default=None, description="Target job description identifier")
    match_result: Optional[MatchResult] = Field(
        default=None,
        description="Deterministic MatchResult from M3 engine when match is executed",
    )
    trigger: str = Field(default="automatic", description="Trigger mechanism (automatic or manual)")
    documents_ready: bool = Field(default=False, description="Whether both required documents are available")
    summary_markdown: Optional[str] = Field(default=None, description="Factual proactive match summary")
    message: Optional[str] = Field(default=None, description="Diagnostic message or error description")

    def to_dict(self) -> Dict[str, Any]:
        """Convenience serializer to dictionary."""
        return self.model_dump(mode="json")


def format_match_summary_markdown(match_result: MatchResult) -> str:
    """
    Renders the factual, evidence-based Candidate Match Summary.
    
    Guarantees:
    - Zero subjective scores (no 82%).
    - Zero tiers (no 'Strong candidate').
    - Zero employment/hiring decisions (no 'Hire' or 'Reject').
    - Clear checkmarks for matched skills and bullets for missing skills.
    - Full resume evidence linking for verified matches.
    """
    lines = [
        "### Candidate Match Summary",
        "",
        f"**Candidate**: {match_result.candidate_id}",
        f"**Position**: {match_result.job_id}",
        "",
        "#### Matched Skills",
    ]

    if match_result.matched_skills:
        for skill in match_result.matched_skills:
            lines.append(f"✓ {skill}")
    else:
        lines.append("*(No verified skill matches found)*")

    lines.extend([
        "",
        "#### Missing Skills",
    ])

    if match_result.missing_skills:
        for skill in match_result.missing_skills:
            lines.append(f"• {skill}")
    else:
        lines.append("*(No missing required skills)*")

    lines.extend([
        "",
        "#### Evidence",
    ])

    if match_result.matched_evidence:
        # Group evidence excerpts briefly
        seen_skills = set()
        for ev in match_result.matched_evidence:
            if ev.skill not in seen_skills:
                seen_skills.add(ev.skill)
                page_str = f"Page {ev.page + 1}" if ev.page is not None else "Indexed Record"
                src_str = ev.source or f"resume_{match_result.candidate_id}.pdf"
                clean_excerpt = (ev.excerpt or "").replace("\n", " ").strip()
                if len(clean_excerpt) > 120:
                    clean_excerpt = clean_excerpt[:117] + "..."
                lines.append(f"• **{ev.skill}**: \"{clean_excerpt}\" *({src_str}, {page_str})*")
    else:
        lines.append("• No resume citations available.")

    lines.extend([
        "",
        "#### Status",
        match_result.status.capitalize() if match_result.status else "Complete",
    ])

    return "\n".join(lines)
