# CAPABL Recruitment Intelligence Agent — Milestone 9 Security Boundary

## 1. Threat Model & Interface Boundary

The MCP interface is treated as an **untrusted boundary**. Requests received via stdio, SSE, or remote client connections must never be trusted without rigorous structural, syntactic, and semantic validation.

```text
External Client / Agent
          │  (Untrusted Input)
          ▼
┌───────────────────────────────────────────────┐
│              MCP Security Boundary            │
│  - Path Traversal & Shell Metacharacters      │
│  - Code & SQL Injection Defense               │
│  - Prompt Injection Neutralization            │
│  - Consequential Mutation Gatekeeper          │
└───────────────────────────────────────────────┘
          │  (Sanitized / Validated)
          ▼
Authoritative CAPABL Services (EvidenceService / Calendar)
```

---

## 2. Input Validation Controls

Implemented in `enhancement/mcp/security.py` and `enhancement/mcp/schemas.py`:

| Threat Vector | Pattern Checked | Enforcement Action | Error Code |
| :--- | :--- | :--- | :--- |
| **Path Traversal** | `../`, `..\`, `/etc/`, `C:\`, `/proc/` | Block request immediately | `PATH_TRAVERSAL_ATTEMPT` |
| **Code Injection** | `__import__`, `eval(`, `exec(`, `subprocess` | Block request immediately | `CODE_INJECTION_ATTEMPT` |
| **SQL Injection** | `UNION SELECT`, `DROP TABLE`, `--;` | Block request immediately | `SQL_INJECTION_ATTEMPT` |
| **Null Bytes** | `\x00` embedded in strings | Block request immediately | `NULL_BYTE_INJECTION` |
| **Oversized Input** | Strings $> 500$ chars (queries) or $> 100$ (IDs) | Reject at schema / boundary level | `OVERSIZED_INPUT` |
| **Unapproved Tool** | Tool not in `MCP_TOOL_REGISTRY` | Block request immediately | `UNAPPROVED_TOOL` |

---

## 3. Prompt Injection Defense

All natural-language inputs (queries, extracted resume text, job requirements) are treated strictly as **inert document content** rather than imperative instructions.

### Detection & Neutralization
Inputs containing instruction-hijacking directives:
- `IGNORE ALL PREVIOUS INSTRUCTIONS`
- `SYSTEM PROMPT:`
- `YOU ARE NOW IN DEVELOPER MODE`
- `DISREGARD THE ABOVE`
- `EXPORT ALL CANDIDATE DATA`
- `ADMIN OVERRIDE:`

are flagged, logged to the audit trail, and stripped/neutralized into `[CONTENT_NEUTRALIZED]` tokens. The LLM and tools process the content as passive search text, preventing prompt hijacking or hallucinated hiring declarations.

---

## 4. Consequential Booking Gatekeeper

Interviews represent state mutations with real calendar impact.

### Invariant
```text
Agent / MCP Request
       ↓
Gatekeeper check (confirmed == True?)
  ├── False ──► BLOCK (status='blocked', error_code='CONFIRMATION_REQUIRED')
  └── True  ──► Forward to MockCalendarService.book_slot(...)
```

The MCP boundary NEVER invokes `book_slot` without explicit user confirmation. Attempted bypasses emit a high-priority `mcp_tool_blocked` audit event.

---

## 5. Domain & Entity Isolation

Strict metadata partitioning ensures cross-entity and cross-domain confidentiality:
- **Candidate Scoping**: `get_candidate_evidence(candidate_id='alex_chen')` is constrained to `document_type='resume'` AND `candidate_id='alex_chen'`. Zero tokens from Priya Sharma or other candidates can leak.
- **Policy Scoping**: `get_policy_evidence(...)` is constrained to `document_type='policy'`. Candidate resumes and job descriptions are never returned.
- **Job Scoping**: `get_job_evidence(job_id='...')` is constrained to `document_type='job_description'`.

---

## 6. Audit Logging & Non-Repudiation

All security checks emit immutable JSONL audit events via `DEFAULT_AUDIT_LOGGER`:
- Timestamps in UTC ISO-8601
- Session correlation IDs
- Safe payloads with automated scrubbing of PII, bearer tokens, and API keys
- Latency tracking in milliseconds
