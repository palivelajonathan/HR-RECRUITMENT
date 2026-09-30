"""
Deterministic Resume-to-JD Match Tool.

CAPABL Track 6 Requirement:
- Deterministic LangChain @tool wrapping the deterministic matching engine.
- Rejects loose LLM generative guesswork for matching skills.
- Strictly returns factual matched skills, missing skills, verified resume citations, and status.
- Zero subjective scores, arbitrary percentages (no 82%), or hiring/rejection labels.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool, BaseTool

from capabl_core.rag.retriever import RecruitmentRetriever
from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.matching import (
    MatchResult,
    run_match,
    compute_deterministic_match,
)


class MatchResumeToJobInput(BaseModel):
    """Input schema for deterministic Resume-to-JD match tool."""
    candidate_id: str = Field(
        ...,
        description="Unique identifier of candidate (e.g., 'alex_chen', 'cand_alex_chen', or resume document ID).",
    )
    job_id: str = Field(
        ...,
        description="Unique identifier of job description (e.g., 'jd_backend_lead_2026', 'jd_senior_backend_lead', or JD document ID).",
    )


# Alias for backward compatibility
MatchInputSchema = MatchResumeToJobInput


def create_match_tool(
    retriever: Optional[RecruitmentRetriever] = None,
    vectorstore_manager: Optional[ChromaVectorStoreManager] = None,
) -> BaseTool:
    """
    Factory function creating an isolated match_resume_to_job LangChain tool.
    Allows injecting custom retrievers or vector store managers for testing.
    """
    @tool("match_resume_to_job", args_schema=MatchResumeToJobInput)
    def match_tool_instance(candidate_id: str, job_id: str) -> Dict[str, Any]:
        """
        Deterministically match an indexed candidate resume against a target job description.
        Computes factual matched skills and missing skills using set operations with source evidence.
        Does NOT invent scores or make hiring decisions.
        """
        try:
            result: MatchResult = run_match(
                candidate_id=candidate_id,
                job_id=job_id,
                retriever=retriever,
                vectorstore_manager=vectorstore_manager,
            )
            return result.to_dict()
        except Exception as exc:
            return {
                "candidate_id": candidate_id,
                "job_id": job_id,
                "status": "error",
                "message": f"Deterministic match engine error: {str(exc)}",
                "matched_skills": [],
                "missing_skills": [],
                "matched_evidence": [],
                "candidate_skills": [],
                "required_skills": [],
            }

    return match_tool_instance


# Default singleton instance
match_resume_to_job = create_match_tool()

__all__ = [
    "MatchResumeToJobInput",
    "MatchInputSchema",
    "match_resume_to_job",
    "create_match_tool",
    "compute_deterministic_match",
]
