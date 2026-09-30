# Tool Contracts & Schemas
**Project**: Recruitment Intelligence Agent  
**Track**: CAPABL Track 6 — HR / Recruitment  
**Status**: ACTIVE INTERFACE DEFINITION  

---

## 1. Overview

Every tool available to the ReAct agent is defined using the LangChain `@tool` decorator with strict Pydantic argument schemas. All inputs and outputs must validate against these contracts. Non-conforming responses raise validation exceptions that are caught and presented as structured tool observations.

---

## 2. Tool 1: `retrieve_evidence` (Metadata-Aware Isolation RAG) — [ACTIVE M2]

### 2.1 Description
Searches the persistent Chroma vector store for verified evidence from `resume`, `job_description`, or `policy` documents. Enforces strict document-type isolation and emits structured evidence summaries.

### 2.2 Input Contract (Pydantic Schema)
```python
from pydantic import BaseModel, Field
from typing import Literal

class RetrievalQueryInput(BaseModel):
    query: str = Field(
        ..., 
        description="Factual semantic search query to look up in the verified knowledge base."
    )
    document_type: Literal["resume", "job_description", "policy"] = Field(
        ..., 
        description="The document category to search. Must strictly be 'resume', 'job_description', or 'policy'."
    )
    top_k: int = Field(
        default=4, 
        ge=1, 
        le=10, 
        description="Maximum number of evidence chunks to retrieve (1-10)."
    )
```

### 2.3 Output Contract (Structured JSON)
```python
{
    "status": "success",  # "success" | "no_evidence" | "error"
    "document_type": "resume",
    "count": 1,
    "results": [
        {
            "content": "7+ years distributed systems...",
            "source": "data/sample/resumes/resume_alex_chen.pdf",
            "page": 0,
            "document_id": "alex_chen",
            "candidate_id": "alex_chen"
        }
    ],
    "message": "Optional diagnostic message when no evidence found or on error."
}
```

---

## 3. Tool 2: `get_candidate_profile_info` (Safe Demonstration Lookup) — [ACTIVE M2]

### 3.1 Description
Safe deterministic tool providing structured candidate overview metadata from registered sample profiles. Proves multi-tool selection without executing external actions or scheduling side-effects.

### 3.2 Input Contract (Pydantic Schema)
```python
from pydantic import BaseModel, Field

class CandidateInfoInput(BaseModel):
    candidate_id: str = Field(
        ..., 
        description="The unique candidate identifier to look up (e.g. 'alex_chen', 'priya_sharma')."
    )
```

### 3.3 Output Contract (Structured JSON)
```python
{
    "status": "success",  # "success" | "not_found"
    "candidate_id": "alex_chen",
    "profile": {
        "candidate_id": "alex_chen",
        "name": "Alex Chen",
        "role_title": "Senior Backend & Distributed Systems Engineer",
        "source_document": "data/sample/resumes/resume_alex_chen.pdf",
        "document_type": "resume",
        "primary_stack": ["Python", "FastAPI", "Kubernetes", "PostgreSQL", "Kafka", "Docker"],
        "status": "active_applicant"
    },
    "message": "Profile found for candidate 'alex_chen'."
}
```

---

## 4. Tool 3: `match_resume_to_job` — [IMPLEMENTED & TESTED (M3)]

### 4.1 Description
Executes a deterministic, set-based evaluation comparing an indexed candidate resume against a target Job Description. Identifies matched requirements and missing skills with verified source citations. Does not invent subjective scores, qualification percentages, or hiring/rejection labels.

### 4.2 Input Contract (Pydantic Schema: `MatchResumeToJobInput`)
```python
class MatchResumeToJobInput(BaseModel):
    candidate_id: str = Field(
        ..., 
        description="Unique identifier of candidate (e.g. 'alex_chen', 'cand_alex_chen', or resume document ID)."
    )
    job_id: str = Field(
        ..., 
        description="Unique identifier of job description (e.g. 'jd_backend_lead_2026', 'jd_senior_backend_lead', or JD document ID)."
    )
```

### 4.3 Output Contract (`MatchResult`)
```json
{
    "candidate_id": "alex_chen",
    "job_id": "jd_backend_lead_2026",
    "matched_skills": ["docker", "fastapi", "kubernetes", "microservices", "postgresql", "python", "redis"],
    "missing_skills": ["rest"],
    "matched_evidence": [
        {
            "skill": "python",
            "source": "data/sample/resumes/resume_alex_chen.pdf",
            "page": 0,
            "document_id": "alex_chen",
            "excerpt": "Core Technical Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis..."
        },
        {
            "skill": "fastapi",
            "source": "data/sample/resumes/resume_alex_chen.pdf",
            "page": 0,
            "document_id": "alex_chen",
            "excerpt": "Architected microservices with Python and FastAPI handling 45,000 requests/sec."
        }
    ],
    "candidate_skills": ["docker", "fastapi", "kubernetes", "microservices", "postgresql", "python", "redis"],
    "required_skills": ["docker", "fastapi", "kubernetes", "microservices", "postgresql", "python", "redis", "rest"],
    "status": "complete",
    "message": "Deterministic match evaluation completed successfully."
}
```

### 4.4 Error & Insufficient Evidence Contract
```json
{
    "candidate_id": "nonexistent_cand",
    "job_id": "jd_backend_lead_2026",
    "matched_skills": [],
    "missing_skills": [],
    "matched_evidence": [],
    "candidate_skills": [],
    "required_skills": [],
    "status": "insufficient_evidence",
    "message": "Could not locate candidate resume 'nonexistent_cand' in indexed records."
}
```

---

## 5. Tool 4: `search_interview_slots` (Non-Consequential Query Tool) — [ACTIVE M4]

### 5.1 Description
Searches the deterministic mock interview calendar for available interview slots. Non-consequential query tool that can be invoked autonomously by the agent. Supports multi-attribute filtering by candidate, job, date, date range, duration, and target timezone.

### 5.2 Input Contract (Pydantic Schema)
```python
from pydantic import BaseModel, Field
from typing import Optional

class SearchSlotsInput(BaseModel):
    candidate_id: Optional[str] = Field(
        default=None,
        description="Candidate ID to filter available slots for (e.g. 'alex_chen')."
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Job ID to filter available slots for (e.g. 'jd_backend_lead_2026')."
    )
    date: Optional[str] = Field(
        default=None,
        description="Specific target date in YYYY-MM-DD format (e.g. '2026-09-29')."
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Optional start date range filter in YYYY-MM-DD format."
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Optional end date range filter in YYYY-MM-DD format."
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Filter by slot duration in minutes (e.g. 30, 45, 60)."
    )
    timezone: Optional[str] = Field(
        default="Asia/Kolkata",
        description="Target timezone string identifier (defaults to 'Asia/Kolkata')."
    )
```

### 5.3 Output Contract (Structured JSON)
```python
{
    "status": "success",  # "success" | "no_slots" | "invalid_request" | "error"
    "candidate_id": "alex_chen",
    "job_id": "jd_backend_lead_2026",
    "timezone": "Asia/Kolkata",
    "total_slots_found": 3,
    "slots": [
        {
            "slot_id": "slot_001",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "start_time": "2026-09-29T10:00:00+05:30",
            "end_time": "2026-09-29T10:30:00+05:30",
            "display_time": "Tuesday, 29 September 2026 10:00 AM - 10:30 AM Asia/Kolkata",
            "timezone": "Asia/Kolkata",
            "duration_minutes": 30,
            "status": "available",
            "interviewer_name": "Vikram Malhotra",
            "interviewer_role": "Engineering Director"
        }
    ],
    "message": "Found 3 available interview slot(s)."
}
```

---

## 6. Tool 5: `book_interview` (Consequential State-Mutation Tool) — [ACTIVE M4]

### 6.1 Description
Atomically books an available interview slot in the mock calendar. Consequential state-mutation tool that strictly requires explicit user confirmation (`confirmed: bool = True`). Enforces validation of slot existence, candidate match, job match, and duplicate booking prevention.

### 6.2 Input Contract (Pydantic Schema)
```python
from pydantic import BaseModel, Field
from typing import Optional

class BookInterviewInput(BaseModel):
    slot_id: str = Field(
        ...,
        description="Unique slot identifier to book (e.g. 'slot_001')."
    )
    candidate_id: str = Field(
        ...,
        description="Unique candidate identifier (e.g. 'alex_chen')."
    )
    job_id: str = Field(
        ...,
        description="Unique job identifier (e.g. 'jd_backend_lead_2026')."
    )
    confirmed: bool = Field(
        default=False,
        description=(
            "Explicit user confirmation flag. Must be explicitly True. "
            "If False, booking is rejected with status 'confirmation_required'."
        )
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional recruiter notes for the interview session."
    )
```

### 6.3 Output Contract (Structured JSON)

**Case A: Confirmed Booking Success**
```python
{
    "status": "success",
    "message": "Interview successfully confirmed and booked for alex_chen (Tuesday, 29 September 2026 from 10:00 AM to 10:30 AM IST) with Vikram Malhotra (Engineering Director). Booking ID: book_slot_001_1790065395.",
    "booking": {
        "booking_id": "book_slot_001_1790065395",
        "slot_id": "slot_001",
        "candidate_id": "alex_chen",
        "job_id": "jd_backend_lead_2026",
        "start_time": "2026-09-29T10:00:00+05:30",
        "end_time": "2026-09-29T10:30:00+05:30",
        "timezone": "Asia/Kolkata",
        "status": "confirmed",
        "created_at": "2026-09-22T13:45:00+05:30",
        "notes": "Verified by hiring manager."
    },
    "slot_id": "slot_001",
    "candidate_id": "alex_chen",
    "job_id": "jd_backend_lead_2026"
}
```

**Case B: Confirmation Required (Zero Mutation)**
```python
{
    "status": "confirmation_required",
    "message": "Explicit user confirmation is required before booking can be executed.",
    "booking": None,
    "slot_id": "slot_001",
    "candidate_id": "alex_chen",
    "job_id": "jd_backend_lead_2026"
}
```

**Case C: Duplicate Booking Rejected (Zero Overwrite)**
```python
{
    "status": "already_booked",
    "message": "Slot 'slot_001' is already booked and cannot be double-booked.",
    "booking": None,
    "slot_id": "slot_001",
    "candidate_id": "alex_chen",
    "job_id": "jd_backend_lead_2026"
}
```

---

## 6. Automatic Match Workflow Contracts (Milestone 5)

The Automatic Match Workflow coordinates the automatic execution of deterministic resume-to-JD matching and proactive summary generation.

### 6.1 Workflow Status & Context Schemas
```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from capabl_core.matching.models import MatchResult

class WorkflowStatus(str, Enum):
    READY = "ready"
    WAITING_FOR_RESUME = "waiting_for_resume"
    WAITING_FOR_JOB_DESCRIPTION = "waiting_for_job_description"
    WAITING_FOR_DOCUMENT = "waiting_for_document"
    ERROR = "error"

class WorkflowContext(BaseModel):
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    resume_path: Optional[str] = None
    job_description_path: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.WAITING_FOR_DOCUMENT
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AutomaticMatchResult(BaseModel):
    status: WorkflowStatus
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    match_result: Optional[MatchResult] = None
    message: str = ""
    markdown_summary: str = ""
```

### 6.2 Output Contract Example (`AutomaticMatchResult`)
```json
{
  "status": "ready",
  "candidate_id": "alex_chen",
  "job_id": "jd_backend_lead_2026",
  "match_result": {
    "candidate_id": "alex_chen",
    "job_id": "jd_backend_lead_2026",
    "matched_skills": ["docker", "fastapi", "kubernetes", "microservices", "postgresql", "python", "redis"],
    "missing_skills": ["rest"],
    "matched_evidence": [
      {
        "skill": "python",
        "source": "data/sample/resumes/resume_alex_chen.pdf",
        "page": 0,
        "document_id": "alex_chen",
        "excerpt": "Core Technical Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis..."
      }
    ],
    "candidate_skills": ["docker", "fastapi", "kubernetes", "microservices", "postgresql", "python", "redis"],
    "required_skills": ["docker", "fastapi", "kubernetes", "microservices", "postgresql", "python", "redis", "rest"],
    "status": "complete",
    "message": "Deterministic match evaluation completed successfully."
  },
  "message": "Automatic match evaluated successfully for candidate 'alex_chen' and job 'jd_backend_lead_2026'.",
  "markdown_summary": "### 🎯 Candidate Match Summary\n**Candidate**: `alex_chen` | **Job**: `jd_backend_lead_2026`\n..."
}
```

---

## 7. Policy & Evidence Layer Tool Contracts (Milestone 6)

Milestone 6 introduces dedicated domain evidence tools to ensure strict isolation between candidate data, job descriptions, and corporate policies.

### 7.1 Data Contracts: `EvidenceItem` and `EvidenceEnvelope`
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum

class PolicyCategory(str, Enum):
    LEAVE_AND_ATTENDANCE = "leave_and_attendance"
    HIRING_PROCESS = "hiring_process"
    COMPENSATION_AND_BENEFITS = "compensation_and_benefits"
    REMOTE_WORK = "remote_work"
    COMPLIANCE_AND_CONDUCT = "compliance_and_conduct"
    GENERAL = "general"

class EvidenceItem(BaseModel):
    content: str
    document_type: Literal["resume", "job_description", "policy"]
    document_id: str
    source: str
    page: int = 0
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    policy_category: Optional[str] = None
    chunk_index: Optional[int] = None
    content_preview: Optional[str] = None

class EvidenceEnvelope(BaseModel):
    status: Literal["success", "no_evidence", "error"]
    target_domain: Literal["policy", "candidate", "job_description", "mixed"]
    query: str
    count: int
    items: List[EvidenceItem] = []
    message: str = ""
```

### 7.2 Tool 5: `retrieve_policy_evidence`
- **Description**: Dedicated tool for querying company HR, recruitment, leave, and conduct policies. Strictly isolated to `document_type="policy"`.
```python
class PolicyEvidenceInput(BaseModel):
    query: str = Field(..., description="Factual query regarding company recruitment, leave, or HR policies.")
    policy_category: Optional[Literal[
        "leave_and_attendance",
        "hiring_process",
        "compensation_and_benefits",
        "remote_work",
        "compliance_and_conduct",
        "general"
    ]] = Field(default=None, description="Optional category filter for corporate policy documents.")
    top_k: int = Field(default=3, ge=1, le=10, description="Maximum number of policy excerpts to retrieve.")
```

### 7.3 Tool 6: `retrieve_candidate_evidence`
- **Description**: Dedicated tool for querying candidate resume experience, education, and skills. Strictly isolated to `document_type="resume"` and scoped to `candidate_id` to prevent cross-candidate leakage.
```python
class CandidateEvidenceInput(BaseModel):
    candidate_id: str = Field(..., description="The unique candidate ID whose resume is being investigated (e.g. 'alex_chen').")
    query: str = Field(..., description="Factual query regarding the candidate's skills, projects, or background.")
    top_k: int = Field(default=3, ge=1, le=10, description="Maximum number of resume excerpts to retrieve.")
```

### 7.4 Tool 7: `retrieve_job_evidence`
- **Description**: Dedicated tool for querying role responsibilities, required qualifications, and interview processes. Strictly isolated to `document_type="job_description"`.
```python
class JobEvidenceInput(BaseModel):
    query: str = Field(..., description="Factual query regarding job responsibilities, requirements, or tech stack.")
    job_id: Optional[str] = Field(default=None, description="Optional job description ID to scope the requirements search.")
    top_k: int = Field(default=3, ge=1, le=10, description="Maximum number of JD excerpts to retrieve.")
```

---

## 8. Milestone 9 Active MCP Tool Contracts & Schemas

In Milestone 9, the external tool boundary is active and enforced via `FastMCP` and `CAPABLMCPClient` in `enhancement/mcp/`.

### 8.1 Approved MCP Tool Registry

| Tool Name | Input Schema | Classification | Sensitivity | Timeout | Gatekeeper |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_candidate_evidence` | `CandidateEvidenceInput` | Read-only | High | 30s | No |
| `get_job_evidence` | `JobEvidenceInput` | Read-only | Medium | 30s | No |
| `get_policy_evidence` | `PolicyEvidenceInput` | Read-only | Medium | 30s | No |
| `search_interview_slots` | `InterviewSearchInput` | Read-only | Low | 30s | No |
| `book_interview` | `BookingInput` | Consequential | High | 30s | **YES (confirmed=True)** |

### 8.2 Standard MCP Response Envelope (`MCPToolResponse`)
Every MCP tool call produces a uniform JSON-serializable envelope:
```json
{
  "status": "success",
  "tool": "get_candidate_evidence",
  "candidate_id": "alex_chen",
  "job_id": null,
  "evidence": [
    {
      "document_type": "resume",
      "document_id": "alex_chen",
      "source": "resume_alex_chen.pdf",
      "page": 0,
      "excerpt": "Core Technical Skills: Python, FastAPI...",
      "candidate_id": "alex_chen",
      "job_id": null,
      "policy_category": null
    }
  ],
  "sources": ["resume_alex_chen.pdf"],
  "data": null,
  "error_code": null,
  "message": "Retrieved 2 resume excerpts for candidate 'alex_chen'."
}
```

For rejected or blocked operations:
```json
{
  "status": "blocked",
  "tool": "book_interview",
  "candidate_id": null,
  "job_id": null,
  "evidence": null,
  "sources": null,
  "data": null,
  "error_code": "CONFIRMATION_REQUIRED",
  "message": "Interview booking for slot 'slot_001' requires explicit user confirmation (confirmed=True)."
}
```
