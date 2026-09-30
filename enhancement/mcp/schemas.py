"""
Pydantic Schemas for MCP Tool Contracts.

Milestone 9: External Tool Integration & MCP Boundary.
Strictly typed, validated input and output schemas for all approved MCP tools.
Rejects malformed, oversized, or unauthorized payloads.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


# Safe identifier regex: alphanumeric, underscores, hyphens only
SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
MAX_QUERY_LENGTH = 500
MAX_ID_LENGTH = 100


class CandidateEvidenceInput(BaseModel):
    """Schema for candidate evidence retrieval via MCP."""
    candidate_id: str = Field(
        ...,
        description="Unique identifier of candidate (e.g. 'alex_chen', 'priya_sharma').",
        min_length=1,
        max_length=MAX_ID_LENGTH,
    )
    query: str = Field(
        ...,
        description="Factual semantic search query for resume qualifications.",
        min_length=1,
        max_length=MAX_QUERY_LENGTH,
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of excerpts to retrieve (1-10).",
    )

    @field_validator("candidate_id")
    @classmethod
    def validate_candidate_id(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("candidate_id cannot be blank")
        if not SAFE_ID_PATTERN.match(v_stripped):
            raise ValueError(f"Invalid candidate_id format: '{v_stripped}'. Must be alphanumeric with underscores/hyphens.")
        return v_stripped

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("query cannot be blank")
        return v_stripped


class JobEvidenceInput(BaseModel):
    """Schema for job description evidence retrieval via MCP."""
    job_id: str = Field(
        ...,
        description="Unique identifier of job description (e.g. 'jd_backend_lead_2026').",
        min_length=1,
        max_length=MAX_ID_LENGTH,
    )
    query: str = Field(
        ...,
        description="Factual search query for job requirements, skills, or responsibilities.",
        min_length=1,
        max_length=MAX_QUERY_LENGTH,
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of excerpts to retrieve (1-10).",
    )

    @field_validator("job_id")
    @classmethod
    def validate_job_id(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("job_id cannot be blank")
        if not SAFE_ID_PATTERN.match(v_stripped):
            raise ValueError(f"Invalid job_id format: '{v_stripped}'. Must be alphanumeric with underscores/hyphens.")
        return v_stripped

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("query cannot be blank")
        return v_stripped


class PolicyEvidenceInput(BaseModel):
    """Schema for company policy evidence retrieval via MCP."""
    query: str = Field(
        ...,
        description="Factual query regarding company HR, compensation, benefits, or hiring policy.",
        min_length=1,
        max_length=MAX_QUERY_LENGTH,
    )
    category: Optional[str] = Field(
        default=None,
        description="Optional policy category filter (e.g. 'compensation', 'leave', 'hiring').",
        max_length=100,
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of policy excerpts to retrieve (1-10).",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("query cannot be blank")
        return v_stripped


class InterviewSearchInput(BaseModel):
    """Schema for querying available interview slots via MCP."""
    candidate_id: Optional[str] = Field(
        default=None,
        description="Optional candidate ID filter.",
        max_length=MAX_ID_LENGTH,
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Optional job ID filter.",
        max_length=MAX_ID_LENGTH,
    )
    date: Optional[str] = Field(
        default=None,
        description="Target date in YYYY-MM-DD format.",
        max_length=20,
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date range in YYYY-MM-DD format.",
        max_length=20,
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date range in YYYY-MM-DD format.",
        max_length=20,
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        ge=15,
        le=180,
        description="Filter by slot duration in minutes.",
    )
    timezone: Optional[str] = Field(
        default="Asia/Kolkata",
        description="Timezone identifier.",
        max_length=50,
    )


class BookingInput(BaseModel):
    """
    Schema for booking an interview slot via MCP.
    Consequential state-changing operation requiring explicit user confirmation.
    """
    slot_id: str = Field(
        ...,
        description="Target slot identifier (e.g. 'slot_001').",
        min_length=1,
        max_length=MAX_ID_LENGTH,
    )
    candidate_id: str = Field(
        ...,
        description="Candidate identifier (e.g. 'alex_chen').",
        min_length=1,
        max_length=MAX_ID_LENGTH,
    )
    job_id: str = Field(
        ...,
        description="Job identifier (e.g. 'jd_backend_lead_2026').",
        min_length=1,
        max_length=MAX_ID_LENGTH,
    )
    confirmed: bool = Field(
        default=False,
        description="MANDATORY confirmation flag. Must be explicitly True or booking will be blocked.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional interview notes.",
        max_length=1000,
    )

    @field_validator("slot_id", "candidate_id", "job_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("ID fields cannot be blank")
        if not SAFE_ID_PATTERN.match(v_stripped):
            raise ValueError(f"Invalid ID format: '{v_stripped}'. Must be alphanumeric with underscores/hyphens.")
        return v_stripped


class MCPToolResponse(BaseModel):
    """Standardized structured response envelope for all MCP tools."""
    status: str = Field(
        ...,
        description="Status code: 'success', 'blocked', or 'error'.",
    )
    tool: str = Field(
        ...,
        description="Name of the MCP tool that was executed.",
    )
    candidate_id: Optional[str] = Field(
        default=None,
        description="Candidate ID context if applicable.",
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Job ID context if applicable.",
    )
    evidence: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of structured evidence items.",
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description="Unique source document names / citations.",
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Arbitrary structured data payload for non-evidence responses.",
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Standardized error category if status != 'success'.",
    )
    message: Optional[str] = Field(
        default=None,
        description="User-safe descriptive message or summary.",
    )

    @classmethod
    def success(
        cls,
        tool: str,
        evidence: Optional[List[Dict[str, Any]]] = None,
        sources: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> "MCPToolResponse":
        return cls(
            status="success",
            tool=tool,
            candidate_id=candidate_id,
            job_id=job_id,
            evidence=evidence,
            sources=sources,
            data=data,
            message=message,
        )

    @classmethod
    def blocked(
        cls,
        tool: str,
        message: str,
        error_code: str = "CONFIRMATION_REQUIRED",
        data: Optional[Dict[str, Any]] = None,
    ) -> "MCPToolResponse":
        return cls(
            status="blocked",
            tool=tool,
            error_code=error_code,
            message=message,
            data=data,
        )

    @classmethod
    def error(
        cls,
        tool: str,
        message: str,
        error_code: str = "INTERNAL_ERROR",
    ) -> "MCPToolResponse":
        return cls(
            status="error",
            tool=tool,
            error_code=error_code,
            message=message,
        )
