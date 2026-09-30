# System Contract: Recruitment Intelligence Agent
**Track**: CAPABL Track 6 — HR / Recruitment  
**Project**: Recruitment Intelligence Agent  
**Status**: ACTIVE CONTRACT — MILESTONE 0 (INITIALIZATION)  
**Lead Architect**: DeepMind Advanced Agentic Coding Pair  

---

## 1. Purpose & Scope

The **Recruitment Intelligence Agent** is an autonomous, deterministic, and privacy-preserving agentic AI system designed for corporate recruitment teams, talent sourcers, and hiring managers. Its primary mission is to automate the end-to-end candidate screening lifecycle:
1. Ingesting and chunking resumes from unstructured PDF formats.
2. Indexing candidate profiles in a vector database with rich, queryable metadata.
3. Conducting metadata-aware semantic retrieval over candidate pools.
4. Performing transparent, mathematical, and deterministic resume-to-job-description (JD) scoring (eliminating generative hallucinations in qualification ratings).
5. Interfacing with calendar services to identify openings and schedule candidate interviews.
6. Providing an intuitive, interactive recruiter dashboard via Streamlit.

---

## 2. Invariant Architectural Principles

### 2.1 The Three-Tier Separation Contract
The codebase strictly enforces three decoupled, non-overlapping architectural layers:

```
+-------------------------------------------------------------------------+
|                       TIER 1: CAPABL CORE                              |
|  - Mandatory Hackathon Stack (LangChain, ChatOllama, PyPDFLoader,       |
|    RecursiveSplitter, BGE Embeddings, Chroma, @tool, create_agent,     |
|    ReAct Loop, Deterministic Match, Calendar Tool, Streamlit UI)       |
+-------------------------------------------------------------------------+
                                    ^
                                    | (Wraps / Intercepts / Enriches)
+-------------------------------------------------------------------------+
|                    TIER 2: ENHANCEMENT LAYER                           |
|  - NAINA-style Multi-step Orchestrator, Structured Cross-Turn Memory,   |
|    Security Gatekeeper & Prompt Guardrails, Dynamic Tool Registry,      |
|    Tamper-Evident Audit Logging, Comprehensive RAG Evaluator            |
|  - Future Extensions: FastMCP Server, n8n Webhook Triggers              |
+-------------------------------------------------------------------------+
                                    ^
                                    | (Deploys / Isolates / Runs)
+-------------------------------------------------------------------------+
|                    TIER 3: INFRASTRUCTURE                              |
|  - Local Containerization (Docker, Docker Compose)                      |
|  - Cloud-Native Orchestration (Kubernetes Deployments, PVCs, Ingress)   |
|  - Health Probes, Storage Persistence, Secrets Management              |
+-------------------------------------------------------------------------+
```

1. **CAPABL Core must remain self-contained**: The core must be executable independently without requiring the Enhancement Layer or Kubernetes. Under no circumstances should enhancement dependencies leak into baseline CAPABL core imports.
2. **Enhancement Layer functions via Decoupled Hooks**: Enhancements (Gatekeeper, Audit Logger, Memory, Orchestrator) wrap or observe core operations using standard interfaces (e.g., decorator patterns, callbacks, or higher-order executors).
3. **Infrastructure provides Environment Abstraction**: Infrastructure defines reproducible runtime containers, volumes, and deployment definitions without embedding business logic.

---

## 3. Mandatory Component Contracts

### 3.1 LLM & Inference Contract: Dual Provider Strategy
The system implements a decoupled LLM provider abstraction managed via `create_llm()` (`capabl_core/llm/`):

1. **Development & Local Testing (CAPABL Core Required)**:
   - **Stack**: `LangChain` -> `ChatOllama` -> `Ollama` -> `Qwen 3 8B` -> `Local GPU`.
   - **Local Model**: `qwen3:8b` (via `OLLAMA_MODEL`).
   - **Data Privacy & Invariance**: 100% offline local inference ensuring complete candidate PII data residency and zero external network overhead.
   - **CAPABL Compliance**: > *ChatOllama remains part of the CAPABL-required core. Groq is an additional deployment provider and does not replace the CAPABL-required ChatOllama implementation.*

2. **Public Deployment (Hosted Inference)**:
   - **Stack**: `LangChain` -> `ChatGroq` -> `Groq API` -> `Configured Hosted Model`.
   - **Configurable Model**: Configured via `GROQ_MODEL` and `GROQ_API_KEY`. No hosted model name is hard-coded into source code.
   - **Operational Purpose**: Enables high-throughput, low-latency live web demonstrations without requiring costly dedicated cloud GPU infrastructure.

3. **Provider Independence Contract**:
   - The agent executor and all downstream subsystems (RAG, Chroma, Retrievers, Deterministic Match Tool, Mock Calendar Tool, Memory, Gatekeeper, Orchestrator, Evaluation, Streamlit UI) depend strictly on LangChain's abstract `BaseChatModel`.
   - Selection between `ollama` and `groq` is explicit via `LLM_PROVIDER`. Silent fallbacks between providers are strictly prohibited.
   - **Determinism Constraint**: Core system prompts and tool calling mandate low temperature ($\le 0.1$) to prevent non-deterministic tool parameter emission.

### 3.2 Ingestion & Vector Retrieval Contract
- **Ingestion**: Documents must be loaded using `PyPDFLoader` and parsed into granular segments using `RecursiveCharacterTextSplitter`.
- **Chunk Size / Overlap**: Default chunk size is 800 characters with 150 character overlap.
- **Embeddings**: Local HuggingFace sentence-transformers (`BAAI/bge-small-en-v1.5` or `BAAI/bge-base-en-v1.5`).
- **Vector Store**: `Chroma` with on-disk directory persistence (`./data/chroma_db`).
- **Metadata Tagging**: Every chunk must carry metadata containing at least: `candidate_id`, `source_file`, `skills_extracted`, `experience_years`, and `ingestion_timestamp`.
- **Retrieval**: Must support hybrid filtering (e.g., vector similarity search combined with metadata boolean constraints).

### 3.3 Deterministic Match Tool Contract
- **Hallucination Ban**: Under no circumstances shall an LLM generate arbitrary numeric match percentages, qualification scores, hiring tiers, or hiring/rejection recommendations.
- **Algorithm Guarantee**: Skill matching is purely deterministic set-based comparison in Python:
  $$\text{matched} = \text{required} \cap \text{candidate}$$
  $$\text{missing} = \text{required} \setminus \text{candidate}$$
  There are NO weighted hiring scores, NO percentage scores, and NO subjective tiers.
- **Factual Match Breakdown**: Every match result returns an exact, auditable breakdown of:
  - Matched required skills
  - Missing critical skills
  - Verifiable evidence quotes directly from ingested documents
  - Strict human decision authority (recruiter evaluates and decides)

### 3.4 Calendar Scheduling Contract
- **State Integrity**: All mock calendar operations must be atomic. Double-booking the same interviewer for the same slot time is strictly prevented.
- **Availability Verification**: Before invoking `book_interview`, the agent must verify slot availability via `check_availability`.

---

## 4. Input / Output & API Invariants

1. **Resume Inputs**: Accepts valid PDF files up to 10MB each conforming to standard text-based PDF formats.
2. **Job Description Inputs**: Accepts formatted text, JSON, or Markdown strings specifying required skills, preferred skills, minimum experience years, and role summary.
3. **Structured Outputs**: All tools must produce valid Pydantic models serializable to standard JSON.

---

## 5. Security & Privacy Guarantees

1. **PII Anonymization**: Candidate contact details (email, phone, street address) must be redactable by the Gatekeeper to support unbiased blind screening workflows.
2. **Prompt Injection Defense**: Ingested resume PDF text must be treated as untrusted user input and sanitized against indirect prompt injection attempts.
3. **Immutable Audit Trail**: All agent thoughts, tool calls, and human approvals are written to an append-only JSONL audit log.

---

## 6. Revision & Versioning
Any modification to this contract requires an updated Architecture Decision Record (ADR) in `DESIGN_DECISIONS.md` and explicit sign-off.
