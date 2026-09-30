"""
Candidate Profile Information Tool for the Recruitment Intelligence Agent.

CAPABL Milestone 2 Requirement:
- Second safe deterministic LangChain @tool proving multi-tool calling.
- Exposes structured candidate overview information from indexed sample data.
- Does NOT perform interview booking.
- Does NOT perform deterministic matching.
- Does NOT perform external actions.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool, BaseTool


class CandidateInfoInput(BaseModel):
    """Input schema for candidate profile lookup."""
    candidate_id: str = Field(
        ...,
        description="The unique candidate identifier to look up (e.g. 'alex_chen', 'priya_sharma').",
    )


# Standard verified sample candidates indexed in the system
VERIFIED_CANDIDATE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "alex_chen": {
        "candidate_id": "alex_chen",
        "name": "Alex Chen",
        "role_title": "Senior Backend & Distributed Systems Engineer",
        "source_document": "data/sample/resumes/resume_alex_chen.pdf",
        "document_type": "resume",
        "primary_stack": ["Python", "FastAPI", "Kubernetes", "PostgreSQL", "Kafka", "Docker"],
        "status": "active_applicant",
    },
    "priya_sharma": {
        "candidate_id": "priya_sharma",
        "name": "Priya Sharma",
        "role_title": "Machine Learning Engineer & Data Architect",
        "source_document": "data/sample/resumes/resume_priya_sharma.pdf",
        "document_type": "resume",
        "primary_stack": ["Python", "PyTorch", "MLflow", "FastAPI", "Docker", "PostgreSQL"],
        "status": "active_applicant",
    },
}


def create_candidate_info_tool(
    registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> BaseTool:
    """Factory creating candidate info lookup tool with optional custom registry for testing."""
    active_registry = registry if registry is not None else VERIFIED_CANDIDATE_REGISTRY

    @tool(args_schema=CandidateInfoInput)
    def get_candidate_profile_info(candidate_id: str) -> Dict[str, Any]:
        """
        Look up verified metadata overview for a specific candidate by their candidate_id.
        Returns candidate identifier, verified source document, and high-level role summary.
        Use this tool when you need basic profile confirmation before or after searching resumes.
        """
        normalized_id = candidate_id.strip().lower()
        if normalized_id in active_registry:
            return {
                "status": "success",
                "candidate_id": normalized_id,
                "profile": active_registry[normalized_id],
                "message": f"Profile found for candidate '{normalized_id}'.",
            }

        return {
            "status": "not_found",
            "candidate_id": normalized_id,
            "profile": None,
            "message": (
                f"Candidate '{normalized_id}' not found in registered profiles. "
                f"Candidate profiles are strictly isolated."
            ),
        }

    return get_candidate_profile_info


# Default tool instance
get_candidate_profile_info = create_candidate_info_tool()
