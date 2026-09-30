# CAPABL Recruitment Intelligence Agent — Milestone 9 Architecture

## 1. Overview & Architectural Objective

Milestone 9 introduces a controlled Model Context Protocol (MCP) external tool boundary to the CAPABL Recruitment Intelligence Agent. This provides standard tool contracts for external agents, orchestrators, and clients without altering the frozen M0–M8 foundations.

### Core Architectural Principle: No Business Logic in MCP
MCP is strictly an **interface boundary**, NOT a business logic layer:
```text
Business Logic
      ↓
Existing CAPABL Services (EvidenceService, MockCalendarService)
      ↓
Tool Contract (CandidateEvidenceInput, BookingInput, etc.)
      ↓
MCP Adapter (MCPToolAdapters)
      ↓
MCP Server (FastMCP / stdio / SSE)
```

There is strictly one authoritative implementation of each capability. No business logic, matching formulas, or scheduling rules are duplicated in the MCP layer.

---

## 2. System Architecture

```text
                               Streamlit UI
                                    │
                                    ▼
                         Recruitment Agent (ReAct)
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
          Native CAPABL Tools                  MCP Boundary
                    │                               │
       ┌────────────┼────────────┐        ┌─────────┴─────────┐
       ▼            ▼            ▼        ▼                   ▼
  match_resume  retrieve_*   calendar  CAPABLMCPClient  FastMCP Server
   (M3 Match)   (M6 RAG)    (M4 Gate)     │                   │
                                          └───────► ◄─────────┘
                                                     │
                                            ┌────────┴────────┐
                                            ▼                 ▼
                                    EvidenceService   MockCalendarService
                                    (Chroma DB)       (Asia/Kolkata Gate)
```

---

## 3. Tool Classification & Approved Registry

Only tools with genuine external interoperability value are exposed over MCP. Internal helpers remain internal.

| MCP Tool Name | Classification | Sensitivity | Authorization | Timeout | State Mutation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_candidate_evidence` | Read-only | High | `read` | 30s | No |
| `get_job_evidence` | Read-only | Medium | `read` | 30s | No |
| `get_policy_evidence` | Read-only | Medium | `read` | 30s | No |
| `search_interview_slots` | Read-only | Low | `read` | 30s | No |
| `book_interview` | Consequential | High | `confirmed_booking` | 30s | **Yes (Gated)** |

### Preserved Native CAPABL Tools
All native CAPABL tools remain fully functional and unmutated:
- `match_resume_to_job`: Deterministic M3 set-based matching ($M = R \cap C$, $Missing = R \setminus C$). Zero hallucinated percentages.
- `retrieve_candidate_evidence`: Direct candidate resume search.
- `retrieve_job_evidence`: Direct job description search.
- `retrieve_policy_evidence`: Direct corporate policy search.
- `get_candidate_profile_info`: Structured candidate profile metadata lookup.
- `search_interview_slots`: Direct calendar slot search.
- `book_interview`: Native consequential calendar booking.

---

## 4. MCP Component Structure

```text
enhancement/
└── mcp/
    ├── __init__.py      # Public exports
    ├── server.py        # FastMCP server exposing 5 approved tools
    ├── client.py        # CAPABLMCPClient boundary & LangChain adapters
    ├── registry.py      # Authoritative tool registry and metadata
    ├── schemas.py       # Pydantic input and envelope schemas
    ├── security.py      # Threat validation, prompt injection & gatekeeper
    ├── tools.py         # Adapters delegating to EvidenceService & Calendar
    └── transport.py     # Stdio/SSE transport parameters and timeouts
```

---

## 5. Structured MCP Response Envelope

Every MCP tool execution returns a standardized Pydantic `MCPToolResponse` envelope:
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
      "excerpt": "Core Technical Skills: Python, FastAPI, Docker, Kubernetes...",
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
For blocked or erroneous calls:
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

---

## 6. Audit Trail Integration

All MCP operations automatically emit structured, immutable audit records to `enhancement/security/audit_logger.py`:
- `mcp_tool_requested`: Tool name, target IDs, query length.
- `mcp_tool_executed`: Success status, duration (ms), result counts.
- `mcp_tool_blocked`: Rejection reason (`CONFIRMATION_REQUIRED`, `PATH_TRAVERSAL_ATTEMPT`, `UNAPPROVED_TOOL`).
- `mcp_tool_failed`: Classified exception category and duration.

Zero raw PII, resume text, or API secrets are ever recorded in audit files.

---

## 7. Failure Handling & Timeouts

- **Bounded Execution**: Every MCP call enforces `timeout_seconds = 30` via `enhancement/mcp/transport.py`.
- **Classification**:
  - *Retryable*: Transient transport disconnections, temporary socket saturation.
  - *Non-retryable*: Malformed arguments, schema validation errors, missing candidate IDs, unconfirmed bookings, and security policy rejections.
