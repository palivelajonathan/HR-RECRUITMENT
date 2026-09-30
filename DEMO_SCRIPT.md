# Hackathon Demonstration Script & Presentation Playbook
**Project**: Recruitment Intelligence Agent  
**Track**: CAPABL Track 6 — HR / Recruitment  
**Total Target Demo Duration**: 5–7 minutes  
**Release Candidate**: Milestone 10 (Production Integrated & Live Verified)

---

## Act 1: The Problem & Our Agentic Solution (1 Minute)

- **Speaker**: "Hello judges! Today, corporate recruitment teams face two severe problems with generative AI in HR:
  1. **Hallucination & Flawed Scoring**: Standard LLMs hallucinate numbers, invent subjective percentage scores, and make opaque hiring recommendations that violate employment regulations.
  2. **Fragmented Workflows & Data Exposure**: Recruiters juggle raw PDF parsing, ATS queries, policy handbooks, and interview calendars across disconnected tools while risking candidate PII leakage to cloud providers.
- We built the **Recruitment Intelligence Agent** for CAPABL Track 6. It pairs an autonomous **LangChain ReAct Agent** with **100% deterministic set-based matching ($M = R \cap C$, $G = R \setminus C$)**, **offline Ollama inference (Qwen 3 8B) for complete PII privacy**, **strict evidence/policy isolation**, **confirmation-gated calendar booking**, and an **auditable Model Context Protocol (FastMCP) external tool boundary**."

---

## Act 2: Streamlit Dashboard & 1-Click Demo Quick-Start (1 Minute)

- **Action**: Open the Streamlit dashboard at `http://localhost:8501`.
- **Demonstration**:
  1. Point out the **Header Status Banner**:
     - **Active Provider**: `Ollama (qwen3:8b) (Local GPU)`
     - **System Health**: `Ready & Operational`
     - **Match Engine**: `M3 Deterministic (Set-Based)`
     - **Tool Boundary**: `Native + FastMCP (5 Tools)`
  2. Click **`⚡ Quick-Load Demo: Alex Chen (Backend Lead)`** in the Demo Control Bar:
     - Ingests `resume_alex_chen.pdf` (2 chunks)
     - Ingests `jd_senior_backend_lead.pdf` (3 chunks)
     - Ingests `policy_leave_and_attendance.pdf` (2 chunks)
     - Shows live chunk indexing and automatically triggers the M3 match engine before any user question is asked!

---

## Act 3: Proactive Deterministic Match & Gap Analysis (1.5 Minutes)

- **Action**: Inspect Section 2 (**Deterministic Resume ↔ JD Matching**).
- **Point out the key architectural invariant**:
  - **Zero Subjective Percentages, Rankings, or Hiring Recommendations**: The engine is purely factual and deterministic:
    - **Matched Technical Skills (7)**: `Python`, `FastAPI`, `Docker`, `Kubernetes`, `PostgreSQL`, `Redis`, `Microservices`.
    - **Missing / Unverified Skills (1)**: `REST`.
    - Total Requirements: 8.
  - Expand **"View Full Factual Match Breakdown & Source Citations"** to show page citations from the original PDF resume and JD.
  - **Speaker**: *"Notice the explicit policy disclaimer: Human recruiters retain sole hiring authority. The AI does not make hire/reject decisions."*

---

## Act 4: Grounded Recruiter Agent Console & Follow-Ups (1 Minute)

- **Action**: In Section 4 (**Recruiter Intelligence Console**), click the quick-prompt button:
  > *"Which required skills are missing or unverified for this role?"*
- **Demonstration**:
  1. Click **Execute Agent Analysis**.
  2. The ReAct agent accesses the active match context and generates a grounded response explaining that REST APIs are not explicitly verified, citing the exact requirements from the Job Description.
  3. Show **Tool Activity Log** and **Retrieved Document Sources**: Every single assertion has an auditable source citation with zero hallucinations.

---

## Act 5: Evidence & Policy Explorer via Native & FastMCP Boundary (1 Minute)

- **Action**: In Section 3 (**Evidence & Research Explorer**), switch to the **Corporate Policy Evidence** tab:
  1. Enter query: *"annual leave allowance and core working hours"*
  2. Select execution path: **MCP External Boundary**
  3. Click **Retrieve Policy Evidence**.
  4. Show the retrieved corporate handbook excerpt (24 days annual leave, core hours 10:00 AM - 4:00 PM).
  5. **Highlight Domain Isolation**: Policy data never leaks candidate info; candidate queries never leak policy info.

---

## Act 6: Interview Scheduling & Confirmation Gatekeeper (1.5 Minutes)

- **Action**: In Section 5 (**Interview Scheduling & Confirmation Gatekeeper**):
  1. Click **🔎 Search Available Slots**: Shows available slots in `Asia/Kolkata` with interviewer name, role, date, time, and duration.
  2. Select slot `slot_001` (Vikram Malhotra, Engineering Director).
  3. **Demonstrate Negative Path (The Gatekeeper Block)**:
     - Click **📅 Confirm & Book Interview Slot** *WITHOUT* checking the confirmation box.
     - **Observe on screen**: Strict red warning banner:
       `🛑 GATEKEEPER BLOCKED: Interview booking requires explicit user confirmation (confirmed=True). State mutation was aborted.`
     - Zero calendar state change!
  4. **Demonstrate Positive Path (Confirmed Execution)**:
     - Check `[x] I explicitly confirm booking interview slot 'slot_001' for alex_chen.`
     - Click **📅 Confirm & Book Interview Slot**.
     - **Observe on screen**: Green alert with confirmed Booking ID (e.g. `book_slot_001_1790344984`) and instant calendar status update.
  5. Attempt to book `slot_001` again: Rejected with `already_booked` to prevent double-booking!

---

## Act 7: Real-time Audit Trail & Safe Reset (30 Seconds)

- **Action**: In Section 6 (**System Evaluation & Observability Dashboard**):
  1. View **Real-time Audit Trail**: Shows structured JSONL audit logs for `demo_loaded`, `mcp_tool_requested`, `booking_blocked_unconfirmed`, and `booking_confirmed` with zero secret or PII leakage.
  2. View **Benchmark Evaluation Metrics**: Shows 100% security pass rate and 100% MCP pass rate.
  3. Click **🔄 Reset Demo State (Safe Clear)**:
     - Clears demo bookings, re-opens slot 001, and resets session state safely without deleting persistent vector data.
- **Closing**:
  - *"Thank you! The Recruitment Intelligence Agent delivers privacy, mathematical rigor, and safe human-in-the-loop agentic workflow for enterprise recruitment."*
