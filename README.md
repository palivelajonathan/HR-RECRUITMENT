# Recruitment Intelligence Agent
### CAPABL Agentic AI Hackathon — Track 6: HR / Recruitment

[![Architecture: 3-Tier Decoupled](https://img.shields.io/badge/Architecture-3--Tier%20Decoupled-blue.svg)](ARCHITECTURE.md)
[![CAPABL Track 6: 100% Compliant](https://img.shields.io/badge/CAPABL%20Track%206-100%25%20Compliant-success.svg)](CAPABL_REQUIREMENTS.md)
[![Inference: 100% Local Ollama](https://img.shields.io/badge/Inference-Local%20Ollama%20(Private)-orange.svg)](SYSTEM_CONTRACT.md)
[![Matching: Deterministic](https://img.shields.io/badge/Matching-Deterministic%20(Zero%20Hallucination)-brightgreen.svg)](DESIGN_DECISIONS.md)

---

## 1. Executive Summary

The **Recruitment Intelligence Agent** is an enterprise-grade, privacy-first agentic AI system engineered for corporate talent acquisition teams, technical hiring managers, and recruitment sourcers. 

Operating strictly within the **CAPABL Track 6** mandate, the agent autonomously ingests candidate resumes from PDF documents, indexes them into a high-density Chroma vector store with rich metadata, conducts semantic talent queries, applies an auditable, **deterministic set-based comparison** ($matched = required \cap candidate$, $missing = required \setminus candidate$) to evaluate resume fit against job descriptions without hallucinated percentage scores, and automates interviewer slot reservations through a mock calendar tool with human confirmation gates.

All language model inference is performed entirely offline via **Ollama**, ensuring absolute privacy for candidate personally identifiable information (PII) and zero cloud data leakage.

---

## 2. Mandatory CAPABL Stack Compliance

The system strictly adheres to every mandatory technology prescribed by CAPABL Track 6:

| Component | Mandatory Requirement | Implementation Location |
|---|---|---|
| **Core Runtime** | Python 3.10+ | Root & virtual environment |
| **Agent Framework** | LangChain (`langchain`, `langchain-core`) | `capabl_core/agent/` |
| **LLM Provider (Core)** | Ollama (Local Daemon) | `capabl_core/llm/` (`qwen3:8b` on local GPU) |
| **LLM Interface (Core)** | `ChatOllama` | `capabl_core/llm/factory.py` (Local Dev & Testing) |
| **LLM Interface (Deploy)**| `ChatGroq` | `capabl_core/llm/factory.py` (Public Cloud Deployment) |
| **Document Ingestion**| `PyPDFLoader` (`pypdf`) | `capabl_core/ingestion/pdf_loader.py` |
| **Text Splitter** | `RecursiveCharacterTextSplitter` | `capabl_core/ingestion/pdf_loader.py` |
| **Embeddings** | HuggingFace BGE (`BAAI/bge-small-en-v1.5`) | `capabl_core/rag/embeddings.py` |
| **Vector Store** | Chroma (`chromadb` with persistence) | `capabl_core/rag/vectorstore.py` (`./data/chroma_db`) |
| **Retrieval** | Metadata-Aware RAG | `capabl_core/rag/retriever.py` |
| **Tool Definition** | LangChain `@tool` decorator | `capabl_core/tools/` |
| **Agent Construction**| `create_agent` / Agent Executor | `capabl_core/agent/react_agent.py` |
| **Reasoning Model** | ReAct Pattern (Thought-Action-Observation) | `capabl_core/agent/react_agent.py` |
| **Scoring Tool** | Deterministic Resume-to-JD Match Tool | `capabl_core/tools/match_tool.py` |
| **Calendar Tool** | Mock Interview Calendar Tool | `capabl_core/tools/calendar_tool.py` |
| **User Interface** | Streamlit (`streamlit`) | `capabl_core/ui/app.py` |

> [!NOTE]
> **CAPABL Compliance Invariant**:  
> *ChatOllama remains part of the CAPABL-required core. Groq is an additional deployment provider and does not replace the CAPABL-required ChatOllama implementation.* Local development strictly executes `LangChain` → `ChatOllama` → `Ollama` → `Qwen 3 8B` → `Local GPU`.

---

## 3. Architecture at a Glance

The codebase enforces a strict **three-tier decoupled architecture**:

```
+-------------------------------------------------------------------------+
|                       TIER 1: CAPABL CORE                              |
|  - Baseline requirements: LangChain, ChatOllama, PyPDFLoader, Chroma,   |
|    RecursiveSplitter, BGE Embeddings, Core Tools, Streamlit UI          |
+-------------------------------------------------------------------------+
                                    ^
                                    | (Wraps / Enhances)
+-------------------------------------------------------------------------+
|                    TIER 2: ENHANCEMENT LAYER                           |
|  - NAINA-style Multi-step Orchestrator, Structured Cross-Turn Memory,   |
|    Security Gatekeeper & Prompt Guardrails, Dynamic Tool Registry,      |
|    Tamper-Evident Audit Logging, RAG & Agent Evaluation Harness         |
+-------------------------------------------------------------------------+
                                    ^
                                    | (Containerizes & Deploys)
+-------------------------------------------------------------------------+
|                    TIER 3: INFRASTRUCTURE                              |
|  - Docker Multi-Stage Image, Docker Compose Local Cluster               |
|  - Kubernetes Base Manifests (Deployment, Service, PVCs, Ingress)       |
+-------------------------------------------------------------------------+
```

---

## 4. Repository Structure

```
.
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore specifications
├── pyproject.toml                    # Modern Python packaging configuration
├── requirements.txt                  # Strict dependency lock
├── README.md                         # Project documentation and guide
├── SYSTEM_CONTRACT.md                # System invariants and boundary definitions
├── CAPABL_REQUIREMENTS.md            # Track 6 requirements & traceability matrix
├── ARCHITECTURE.md                   # In-depth architectural design specifications
├── DATA_FLOW.md                      # Sequence diagrams and data lifecycles
├── DESIGN_DECISIONS.md               # Formal Architecture Decision Records (ADRs)
├── TOOL_CONTRACTS.md                 # Pydantic schemas and tool specifications
├── MEMORY.md                         # Memory hierarchy (Short-term, Session, Long-term)
├── SECURITY.md                       # STRIDE threat model & prompt injection defense
├── EVALUATION.md                     # RAG triad metrics and testing benchmarks
├── DEPLOYMENT.md                     # Local and Docker setup instructions
├── DEPLOYMENT_KUBERNETES.md          # Production Kubernetes architecture & manifests
├── DEMO_SCRIPT.md                    # 7-act live hackathon presentation playbook
│
├── capabl_core/                      # TIER 1: CAPABL Core Baseline
│   ├── llm/                          # Dual Provider Abstraction (create_llm, ChatOllama, ChatGroq)
│   ├── ingestion/                    # PyPDFLoader & RecursiveCharacterTextSplitter
│   ├── rag/                          # BGE Embeddings, Chroma store & metadata retriever
│   ├── matching/                     # Deterministic Resume-to-JD Match Engine (M3)
│   │   ├── models.py                 # SkillEvidence & MatchResult contracts
│   │   ├── normalizer.py             # SKILL_ALIASES & canonical normalization
│   │   ├── extractor.py              # Technical skill pattern extraction & JD requirement parsing
│   │   └── matcher.py                # Set-based matching & programmatic run_match() API
│   ├── calendar/                     # Deterministic Mock Interview Calendar Subsystem (M4)
│   │   ├── models.py                 # Timezone-aware InterviewSlot, InterviewBooking, CalendarEvent
│   │   └── service.py                # MockCalendarService with atomic booking & duplicate protection
│   ├── workflow/                     # Automatic Resume + JD Match Workflow Subsystem (M5)
│   │   ├── models.py                 # WorkflowStatus, WorkflowContext, AutomaticMatchResult
│   │   └── service.py                # AutomaticMatchService, readiness check, targeted replacement
│   ├── evidence/                     # Recruitment Intelligence Policy & Evidence Layer (M6)
│   │   ├── models.py                 # EvidenceItem, EvidenceEnvelope, PolicyCategory contracts
│   │   ├── service.py                # EvidenceService with multi-layer domain isolation
│   │   └── router.py                 # Deterministic QueryIntent classifier
│   ├── tools/                        # LangChain @tools (retrieve_evidence, candidate_info, match_resume_to_job, search_interview_slots, book_interview, retrieve_policy_evidence, retrieve_candidate_evidence, retrieve_job_evidence)
│   ├── agent/                        # Provider-independent ReAct agent executor
│   └── ui/                           # Streamlit recruiter dashboard
│
├── enhancement/                      # TIER 2: Enhancement Layer
│   ├── orchestration/                # NAINA-style multi-step workflow coordinator
│   ├── memory/                       # Structured candidate dossier persistence
│   ├── gatekeeper/                   # Ingestion guardrails & prompt injection defense
│   ├── registry/                     # Dynamic tool registry
│   ├── security/                     # Tamper-evident JSONL audit logger
│   ├── evaluation/                   # RAG triad and deterministic scoring evaluator
│   ├── mcp/                          # FastMCP / MultiServerMCPClient (Phased)
│   └── workflow/                     # n8n webhook event dispatcher (Phased)
│
├── infra/                            # TIER 3: Infrastructure
│   ├── docker/                       # Dockerfile and docker-compose.yml
│   └── k8s/base/                     # Kubernetes Deployment, Service, PVC, Ingress
│
├── data/                             # Data and persistence directories
│   ├── resumes/                      # Input PDF candidate resumes
│   ├── job_descriptions/             # Input Job Description files
│   └── chroma_db/                    # Persistent Chroma database files
│
└── tests/                            # Comprehensive Test Suite
    ├── unit/                         # Unit tests (LLM provider, RAG, Agent core, Match engine, Calendar, Workflow, Policy & Evidence)
    ├── integration/                  # End-to-end ReAct loop integration tests
    └── evaluation/                   # Benchmark metrics and evaluation harness
```

---

## 5. Quickstart (Development Mode)

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai) installed and running locally

### 2. Setup Environment
```bash
# Clone the repository
cd "HACKATHON PROJECT CAPABL"

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
# source venv/bin/activate    # On Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Pull local Ollama LLM (Qwen 3 8B)
ollama pull qwen3:8b

# Copy environment configuration
copy .env.example .env        # On Windows
# cp .env.example .env        # On Linux/macOS
```

### 3. Launch the Application
```bash
streamlit run capabl_core/ui/app.py
```
Open your browser at `http://localhost:8501`.

---

## 6. Incremental Roadmap

- [x] **Milestone 0: Architectural Blueprint, Dual LLM Provider & Repository Initialization** (Validated, 8/8 tests passed)
- [x] **Milestone 1: RAG Ingestion Foundation (PyPDFLoader, Document Chunking, BGE Embeddings, Chroma Persistence & Isolation Retriever)** (Validated, 16/16 tests passed)
- [x] **Milestone 2: CAPABL Agent Core + LangChain Tool Calling (create_agent, @tool, retrieve_evidence, get_candidate_profile_info, AgentExecutionResult)** (Validated, 25/25 tests passed)
- [x] **Milestone 3: Deterministic Resume ↔ JD Match Engine (Skill Normalization, Extraction, Set-Based Matching, Evidence Linking, LangChain Tool & Automatic Match API)** (Validated, 36/36 tests passed)
- [x] **Milestone 4: Interview Scheduling Tool (Deterministic Mock Calendar, Timezone-Aware Slots, search_interview_slots, book_interview with Explicit Confirmation Gatekeeper)** (Validated, 56/56 tests passed)
- [x] **Milestone 5: Automatic Resume + JD Match Workflow & Proactive Factual Summarization (Automatic Document Trigger, Targeted Replacement, Chroma Isolation, Proactive Factual Summary, Agent Context Injection)** (Validated, 78/78 tests passed)
- [x] **Milestone 6: Recruitment Intelligence Policy & Evidence Layer (Dedicated Domain Tools: retrieve_policy_evidence, retrieve_candidate_evidence, retrieve_job_evidence; Multi-Layer Isolation; EvidenceItem & EvidenceEnvelope; Deterministic Query Intent Router; Prompt-Injection Resistance & Non-Authoritative Hiring Boundary)** (Validated, 109/109 tests passed)
- [x] **Milestone 6.5: System Stabilization & Remediation (Real PDF Ingestion, Dynamic Provider Resolution, Streamlit Startup Verification, Dependency Lock Synchronization)** (Validated, 128/128 tests passed)
- [x] **Milestone 7: Production Evaluation, Observability & Quality Assurance (Append-Only JSONL Audit Logger, 5 Evaluation Suites: Retrieval, RAG, Tools, Agent, Security; Master CLI Runner; Empirical M7_BASELINE.json; Interactive Streamlit Dashboard; 100% Security Pass Rate)** (Validated, 32/32 evaluation tests passed, 167/167 full regression passed)
- [x] **Milestone 8: Production Hardening, Security & Deployment Readiness (Configuration Hardening, Upload Validation, PII Redaction, Health Probes, Bounded Retries, Chroma Backup/Restore, Security Tests)** (Validated, 208/208 full regression passed)
- [x] **Milestone 9: External Tool Integration & MCP Boundary (FastMCP Server, MCP Client Bridge, Tool Contracts, Prompt Injection Defense, 5 Approved MCP Tools, Bounded Execution)** (Validated, 236/236 full regression passed)
- [x] **Milestone 10: Final Product Integration & Demo Readiness (17-Step Recruiter Journey, Demo Control & Quick-Start Bar, Grounded Synthesis, Calendar Confirmation Gatekeeper, Real-time JSONL Audit Trail, Streamlit UI Verification)** (Validated, 242/242 full regression passed, 17/17 live checkpoints passed)



#   H R - R E C R U I T M E N T  
 