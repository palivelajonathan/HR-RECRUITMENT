# CAPABL Hackathon Requirements & Traceability Matrix
**Track**: CAPABL Track 6 — HR / Recruitment  
**Project**: Recruitment Intelligence Agent  

---

## 1. Track Overview & Objectives

CAPABL Track 6 focuses on building an **autonomous HR & Recruitment Intelligence Agent** capable of assisting hiring teams through parsing, indexing, searching, matching, and scheduling candidate workflows using an agentic, tool-augmented architecture.

---

## 2. Mandatory CAPABL Stack Compliance

The project explicitly adopts and complies with 100% of the prescribed CAPABL technology stack without substitution:

| Mandatory Requirement | Technology / Library | Architectural Role | Status |
|---|---|---|---|
| **Programming Language** | Python 3.10+ | Core development runtime | Initialized |
| **Agent Framework** | LangChain (`langchain`, `langchain-core`) | Agent reasoning loop and tool binding | Implemented & Tested (M2) |
| **LLM Provider (Core)** | Ollama (Local Daemon) | Local open-source inference server (`qwen3:8b`) | Configured |
| **LLM Interface (Core)** | `ChatOllama` | LangChain Chat Model wrapper for Ollama | Implemented & Tested (M0, M2) |
| **LLM Interface (Deploy)**| `ChatGroq` (Groq API) | Additional public deployment provider (Configurable) | Implemented & Tested (M0) |
| **Document Loader** | `PyPDFLoader` (`pypdf`) | Unstructured PDF resume text & metadata extraction | Implemented & Tested (M1) |
| **Text Splitter** | `RecursiveCharacterTextSplitter` | Document-specific semantic chunking with profiles | Implemented & Tested (M1) |
| **Embedding Model** | HuggingFace / BGE (`BAAI/bge-small-en-v1.5`) | High-density semantic vector embeddings (384-d) | Implemented & Tested (M1) |
| **Vector Database** | Chroma (`langchain-chroma`) | Embedded persistent vector storage across restarts | Implemented & Tested (M1) |
| **Retrieval Strategy** | Metadata-Aware RAG | Filtering & document isolation (zero contamination) | Implemented & Tested (M1) |
| **Tool Definition** | LangChain `@tool` decorator | Standardized tool schemas with Pydantic validation | Implemented & Tested (M2) |
| **Agent Construction** | `create_agent` / LangChain Agent Executor | ReAct pattern execution engine | Implemented & Tested (M2) |
| **Agent Reasoning Pattern**| ReAct Loop | Explicit Thought -> Action -> Observation cycle | Implemented & Tested (M2) |
| **Core Tool 1** | Deterministic Match Tool | Non-hallucinatory, set-based Resume-to-JD matching | Implemented & Tested (M3) |
| **Core Tool 2** | Mock Interview Calendar Tool | Availability checking & atomic slot reservation | Implemented & Tested (M4) |
| **Automatic Match Workflow**| Dual Document Trigger & Proactive Summary | Automatic match execution when Resume + JD available | Implemented & Tested (M5) |
| **Evidence & Policy Layer** | Dedicated Domain Tools & Isolation | Evidence routing, strict policy/candidate separation, prompt-injection defense | Implemented & Tested (M6) |
| **User Interface** | Streamlit (`streamlit`) | Interactive web application with proactive match card & agent chat | Implemented & Tested (M5, M6) |

> [!IMPORTANT]
> **CAPABL Compliance Invariant**:  
> *ChatOllama remains part of the CAPABL-required core. Groq is an additional deployment provider and does not replace the CAPABL-required ChatOllama implementation.* The local development pipeline strictly executes: `LangChain` → `ChatOllama` → `Ollama` → `Qwen 3 8B` → `Local GPU`.

---

## 3. Detailed Traceability Matrix

Every CAPABL requirement is strictly mapped to an implementation component, an enhancement hook, an automated verification test, and a live demonstration step:

| Req ID | Requirement Description | Implementation Component | Enhancement Layer Hook | Test Case ID | Demo Step |
|---|---|---|---|---|---|
| **REQ-01** | Load & parse PDF resumes, JDs & policies | `capabl_core/ingestion/pdf_loader.py` | `enhancement/gatekeeper/guardrails.py` (malicious payload scan) | `tests/unit/test_rag_foundation.py` | Demo Step 1: Ingest resumes |
| **REQ-02** | Chunk documents recursively by type | `capabl_core/ingestion/pdf_loader.py` | `enhancement/memory/structured_memory.py` (chunk cataloging) | `tests/unit/test_rag_foundation.py` | Demo Step 1: Chunk viewer |
| **REQ-03** | Generate BGE dense embeddings (384-d) | `capabl_core/rag/embeddings.py` | Performance profiler & batching | `tests/unit/test_rag_foundation.py` | Demo Step 1: Vector generation |
| **REQ-04** | Persist vector store in Chroma | `capabl_core/rag/vectorstore.py` | Volume persistence & index backup | `tests/unit/test_rag_foundation.py` | Demo Step 1: Collection inspect |
| **REQ-05** | Metadata-aware retrieval & isolation | `capabl_core/rag/retriever.py` | Hybrid keyword + vector re-ranking | `tests/unit/test_rag_foundation.py` | Demo Step 2: Filtered query |
| **REQ-06** | Deterministic Resume-JD Match | `capabl_core/matching/` & `capabl_core/tools/match_tool.py` | Explainability audit & bias metrics | `tests/unit/test_match_engine.py` | Demo Step 3: Candidate scoring |
| **REQ-07** | Mock Interview Calendar Booking | `capabl_core/tools/calendar_tool.py` | Double-booking prevention & conflict logging | `tests/unit/test_calendar_tool.py`| Demo Step 4: Schedule interview |
| **REQ-08** | ChatOllama LLM Agent Engine & Dual Provider Factory | `capabl_core/llm/factory.py` & `capabl_core/agent/react_agent.py` | Provider abstraction & ChatGroq public deployment bridge | `tests/unit/test_llm_provider.py`, `tests/unit/test_agent_core.py` | Demo Step 2-4: Agent thoughts |
| **REQ-09** | ReAct Multi-step Reasoning via create_agent | `capabl_core/agent/react_agent.py` | `enhancement/orchestration/naina_orchestrator.py` | `tests/unit/test_agent_core.py` | Demo Step 2-4: Live trace log |
| **REQ-10** | Streamlit Recruiter Dashboard | `capabl_core/ui/app.py` | Audit log telemetry & gatekeeper alerts | `tests/unit/test_automatic_workflow.py` | Demo Step 1-5: Full UI walk |
| **REQ-11** | Automatic Resume + JD Match Trigger & Proactive Summary | `capabl_core/workflow/` & `capabl_core/ui/app.py` | Targeted document replacement & agent context injection | `tests/unit/test_automatic_workflow.py` | Demo Step 3: Proactive match card |
| **REQ-12** | Recruitment Intelligence Policy & Evidence Layer | `capabl_core/evidence/` & `capabl_core/tools/` | Multi-layer domain isolation, structured `EvidenceEnvelope`, untrusted data boundary, prompt-injection defense | `tests/unit/test_policy_and_evidence.py` | Demo Step 2: Policy & evidence Q&A |

---

## 4. Verification Protocol
1. **Red-Green-Refactor Cycle**: For every milestone, unit tests validating tool interfaces and RAG logic will be executed prior to marking milestones as complete.
2. **Deterministic Reproducibility**: Given an identical resume PDF and job description, `match_tool` must return the identical score across repeated executions ($Score_1 == Score_2$).
3. **Traceability Auditing**: No code shall be merged into `main` unless it maps directly to a Requirement ID in this matrix.
