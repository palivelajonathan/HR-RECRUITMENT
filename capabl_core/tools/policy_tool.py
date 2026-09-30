"""
Policy Evidence Retrieval Tool for CAPABL Track 6 (Milestone 6).

LangChain @tool retrieving corporate HR guidelines, leave, attendance,
and workplace policies exclusively from document_type='policy'.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool, BaseTool

from capabl_core.evidence.service import EvidenceService


class PolicyEvidenceInput(BaseModel):
    """Input contract for corporate policy evidence retrieval."""
    query: str = Field(
        ...,
        description="Factual semantic search query regarding company HR policy, leave, attendance, benefits, or guidelines.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Optional policy topic/category to refine the search (e.g. 'leave_and_attendance', 'remote_work').",
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of policy excerpts to retrieve (1-10).",
    )


def create_policy_evidence_tool(
    evidence_service: Optional[EvidenceService] = None,
) -> BaseTool:
    """
    Factory creating a LangChain BaseTool bound to an EvidenceService instance.
    Enables dependency injection for hermetic testing.
    """
    _service: Optional[EvidenceService] = evidence_service

    @tool("retrieve_policy_evidence", args_schema=PolicyEvidenceInput)
    def retrieve_policy_evidence(
        query: str,
        category: Optional[str] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """
        Retrieve verified factual corporate policy evidence exclusively from policy documents.
        Use this tool whenever you need facts about company HR guidelines, annual leave,
        sick leave, core hours, remote work policy, sabbaticals, or benefits.
        Never use this tool to search candidate resumes or job descriptions.
        """
        nonlocal _service
        if _service is None:
            _service = EvidenceService()

        envelope = _service.get_policy_evidence(
            query=query,
            category=category,
            top_k=top_k,
        )
        return envelope.to_tool_dict()

    return retrieve_policy_evidence


# Default instance bound to persistent Chroma store
retrieve_policy_evidence = create_policy_evidence_tool()
