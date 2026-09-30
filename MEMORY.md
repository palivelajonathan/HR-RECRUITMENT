# Memory Architecture & State Management
**Project**: Recruitment Intelligence Agent  
**Track**: CAPABL Track 6 — HR / Recruitment  
**Status**: ARCHITECTURAL SPECIFICATION  

---

## 1. Memory Hierarchy Overview

The Recruitment Intelligence Agent operates with a three-tier memory model:
1. **Tier 1: Short-Term Working Memory (ReAct Scratchpad)** — Scoped to a single user query execution.
2. **Tier 2: Structured Conversational Memory (Session State)** — Scoped to an active recruiter UI session.
3. **Tier 3: Long-Term Candidate Dossier Memory (Persistent Store)** — Cross-session, durable recruitment state.

```
+-------------------------------------------------------------------------+
|                TIER 1: SHORT-TERM WORKING MEMORY                       |
|  - ReAct Scratchpad (Thought, Action, Observation, Thought...)          |
|  - Intermediate tool return values within single query execution        |
|  - Volatile, cleared upon final response emission                       |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|             TIER 2: STRUCTURED CONVERSATION MEMORY (SESSION)            |
|  - Streamlit `st.session_state` / LangChain ConversationBufferMemory   |
|  - Selected Job Description ID, Active Filter Criteria                  |
|  - Current Candidate Shortlist & Comparative Rankings                   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|         TIER 3: LONG-TERM CANDIDATE DOSSIER MEMORY (PERSISTENT)        |
|  - Stored in `./data/memory/candidate_dossiers.json` (or SQLite)        |
|  - Persistent Candidate Dossier (Verified Skills, Historical Matches,   |
|    Interview Booking Records, Recruiter Feedback & Human Decisions)     |
+-------------------------------------------------------------------------+
```

---

## 2. Tier 1: Short-Term Working Memory (ReAct Scratchpad)

- **Lifecycle**: Initialized when a recruiter submits a prompt; destroyed after the agent delivers its final response.
- **Mechanism**: Implemented via LangChain's `AgentAction` and `AgentStep` lists passed into the prompt template.
- **Structure**:
  ```text
  Thought: The recruiter is asking for candidates with 5+ years experience in Python and FastAPI.
  Action: candidate_search
  Action Input: {"query": "Python FastAPI", "required_skills": ["python", "fastapi"], "min_experience_years": 5.0}
  Observation: Found 2 matching profiles: cand_001 (Jane Doe, 6 yrs), cand_004 (Alex Smith, 5 yrs).
  Thought: I now have the candidate profiles. Next, I will compare them against the active Job Description.
  ...
  ```

---

## 3. Tier 2: Structured Conversational Session State

- **Lifecycle**: Persists during a recruiter's browser session.
- **Stored State**:
  - `active_job_description`: The target JD currently undergoing candidate screening.
  - `candidate_shortlist`: Current pool of candidates marked for evaluation.
  - `recent_queries`: History of natural-language recruiter questions in the session.
  - `view_mode`: UI toggle state (e.g., standard view vs. anonymized blind screening view).

---

## 4. Tier 3: Long-Term Candidate Dossier Memory

- **Persistence Target**: `./data/memory/` (JSON / SQLite).
- **Purpose**: Prevent redundant re-parsing and re-scoring of candidates; record full recruitment history.

### Candidate Dossier Schema (JSON)
```json
{
  "candidate_id": "cand_jane_doe_2026",
  "name": "Jane Doe",
  "email_redacted": "j***@domain.com",
  "extracted_skills": ["Python", "Docker", "Kubernetes", "PostgreSQL", "FastAPI", "LangChain"],
  "total_experience_years": 6.5,
  "ingested_at": "2026-09-21T10:15:30Z",
  "evaluations": [
    {
      "job_id": "jd_backend_lead_01",
      "evaluated_at": "2026-09-21T11:00:12Z",
      "overall_match_percentage": 89.2,
      "skill_score": 0.92,
      "experience_score": 1.00,
      "domain_score": 0.75,
      "status": "Shortlisted"
    }
  ],
  "interview_bookings": [
    {
      "confirmation_id": "CONF-89123",
      "interviewer_role": "technical_lead",
      "interviewer_name": "Marcus Vance",
      "scheduled_time": "2026-09-29 14:00",
      "round_type": "Technical Round 1",
      "status": "CONFIRMED"
    }
  ],
  "recruiter_notes": [
    {
      "timestamp": "2026-09-21T11:05:00Z",
      "note": "Strong open-source contributions in Kubernetes tools."
    }
  ]
}
```

---

## 5. Checkpointing & Fault Recovery

For complex multi-stage tasks executed by the **NAINA Orchestrator**, state checkpoints are written before and after any irreversible tool call (e.g. `book_interview_tool`).

If an Ollama daemon connection drops or the browser refreshes:
1. The orchestrator reloads the candidate dossier from `./data/memory/`.
2. Restores the active candidate shortlist.
3. Resumes execution from the last uncommitted pipeline stage without re-running completed embeddings or match calculations.
