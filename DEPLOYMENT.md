# Production Deployment & Operations Guide
**Project**: Recruitment Intelligence Agent  
**Track**: CAPABL Track 6 — HR / Recruitment  
**Milestone**: M8 Hardening & Deployment Readiness  
**Status**: PRODUCTION READY  

---

## 1. Prerequisites

Before deploying the Recruitment Intelligence Agent, ensure your target host or container platform meets the following specifications:
- **Operating System**: Linux (Ubuntu 22.04+ / Debian 12), Windows 10/11, or macOS.
- **Python**: Version 3.10.x.
- **Memory (RAM)**: Minimum 16GB for local Ollama 8B inference; minimum 4GB for public cloud (Groq-backed) containers.
- **Disk Space**: At least 10GB for Ollama model weights, embeddings cache, and Chroma persistent storage.
- **Inference Runtime**:
  - Local / On-Prem: Ollama daemon serving `qwen3:8b` on `http://localhost:11434`.
  - Public Cloud: Groq API key (`gsk_...`) with model `llama-3.3-70b-versatile`.
- **Containerization**: Docker 24.0+ and Docker Compose v2 (optional: Kubernetes 1.28+).

---

## 2. Production Configuration & Boundaries

The application uses `capabl_core.config.settings.ProductionSettings` to enforce environment isolation, strict resource ceilings, and secure defaults.

### 2.1 Core Environment Variables

| Variable | Default | Allowed Values | Purpose |
|---|---|---|---|
| `APP_ENV` | `development` | `development`, `test`, `production` | Environment profile; enforces strict secret validation in production. |
| `LLM_PROVIDER` | `ollama` | `ollama`, `groq` | Primary LLM inference provider. |
| `OLLAMA_MODEL` | `qwen3:8b` | String | Model identifier for Ollama inference. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL | Ollama API endpoint. |
| `GROQ_API_KEY` | None | String (`gsk_...`) | API Key required if `LLM_PROVIDER=groq`. |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | String | Groq model identifier. |
| `CHROMA_PERSIST_DIRECTORY` | `./data/chroma_db` | Path | Persistent SQLite vector database directory. |
| `CHROMA_COLLECTION_NAME` | `recruitment_documents`| String | Active collection name. |
| `AUDIT_LOG_DIR` | `./logs/audit` | Path | Audit trail storage directory. |
| `AUDIT_LOG_PATH` | `./logs/audit/audit_trail.jsonl`| Path | Append-only structured JSONL audit trail. |
| `AUDIT_MAX_BYTES` | `10485760` (10MB) | Integer | Log file rotation ceiling. |
| `AUDIT_BACKUP_COUNT` | `5` | Integer | Rotated log archive count. |
| `MAX_UPLOAD_SIZE_MB` | `10` | Integer | Maximum accepted PDF upload file size. |
| `MAX_PDF_PAGES` | `20` | Integer | Maximum accepted PDF page count. |
| `MAX_DOCUMENT_CHUNKS` | `100` | Integer | Maximum allowable text chunks per document. |
| `MAX_QUERY_LENGTH` | `1000` | Integer | Maximum recruiter query length to prevent buffer overruns. |
| `LLM_TIMEOUT_SECONDS` | `60` | Integer | Timeout ceiling for LLM inference requests. |

---

## 3. Local Bare-Metal Setup (Development Mode)

### Step 3.1: Clone and Configure Environment
```bash
git clone <repo-url>
cd "HACKATHON PROJECT CAPABL"

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy configuration
cp .env.example .env
```

### Step 3.2: Verify Ollama Service
Ensure Ollama is running and has pulled the mandatory default model:
```bash
ollama pull qwen3:8b
ollama list
```

### Step 3.3: Launch Streamlit Dashboard
```bash
streamlit run capabl_core/ui/app.py --server.port 8501 --server.address 0.0.0.0
```
Open `http://localhost:8501` to access the recruitment intelligence UI.

---

## 4. Containerized Deployment (Docker)

The production Docker image (`infra/docker/Dockerfile`) runs as non-root user `appuser` (UID 10001) on a minimal `python:3.10-slim` base image.

### Step 4.1: Build Container Image
```bash
docker build -t recruitment-agent:latest -f infra/docker/Dockerfile .
```

### Step 4.2: Run with Docker Compose
```bash
# Start containerized stack (includes healthcheck)
docker compose -f infra/docker/docker-compose.yml up --build -d

# Check container status
docker compose -f infra/docker/docker-compose.yml ps

# Inspect logs
docker compose -f infra/docker/docker-compose.yml logs -f agent-app
```

---

## 5. Health & Readiness Subsystem

The application exposes dedicated, lightweight health inspection mechanisms:

### 5.1 Process Liveness Probe
Answers: *"Is the Python/Streamlit process running?"*
```python
from capabl_core.health.checks import check_liveness

res = check_liveness()
# Returns: {"status": "healthy", "alive": True, "timestamp": "...", "uptime_seconds": 12.4}
```
HTTP Endpoint: `GET http://localhost:8501/_stcore/health` (HTTP 200).

### 5.2 Application Readiness Probe
Answers: *"Can the application perform search, retrieval, and matching operations?"*
Evaluates:
1. Configuration integrity and environment variables.
2. Chroma SQLite persistence directory read/write access.
3. LLM provider contract validation (without costly generation calls).
4. Storage directories (`./data`, `./logs/audit`).

```python
from capabl_core.health.checks import check_readiness

res = check_readiness()
# Returns: {"status": "ready", "ready": True, "checks": {...}, "timestamp": "..."}
```

---

## 6. Chroma Persistence, Backup & Disaster Recovery

ChromaDB uses an embedded SQLite database and local HNSW index files. Multi-process concurrent writes to the same directory will corrupt the database.

### 6.1 Database Persistence Rules
- Mount a single persistent volume to `/app/data/chroma_db`.
- Never scale deployments to `replicas > 1` when sharing the same volume.

### 6.2 Deterministic Backup Procedure
To create a timestamped, gzip-compressed snapshot of the vector store:
```python
from capabl_core.rag.persistence import create_chroma_backup

backup_file = create_chroma_backup(
    persist_directory="./data/chroma_db",
    backup_file_path="./backups/chroma_backup_20260925.tar.gz"
)
```

### 6.3 Deterministic Restore Procedure
To restore from a backup with tar-slip path traversal protection:
```python
from capabl_core.rag.persistence import restore_chroma_backup

restored_dir = restore_chroma_backup(
    backup_file_path="./backups/chroma_backup_20260925.tar.gz",
    target_directory="./data/chroma_db"
)
```

---

## 7. Audit Log Retention & Rotation

- The audit logger writes append-only JSONL records to `logs/audit/audit_trail.jsonl`.
- PII (emails, phone numbers, SSNs, credit cards) and API credentials are automatically scrubbed via regex before hitting disk.
- Size-based rotation triggers when the file exceeds `AUDIT_MAX_BYTES` (default 10MB), retaining up to `AUDIT_BACKUP_COUNT` (default 5) archives (`audit_trail.jsonl.1` through `.5`).

---

## 8. Deployment Verification

Run the master M8 deployment smoke verification script to validate all 15 production checkpoints:
```bash
python scripts/verify_m8_deployment.py
```
Expected output:
```text
DEPLOYMENT SMOKE TEST RESULT: 15/15 CHECKPOINTS PASSED
[SUCCESS] ALL 15 DEPLOYMENT CHECKPOINTS PASSED. SYSTEM IS DEPLOYMENT & PRODUCTION READY.
```

---

## 9. Milestone 9 MCP External Tool Server Deployment

Milestone 9 introduces the standalone FastMCP server for standard external tool consumption:

### 9.1 Running the FastMCP Server (stdio / SSE)
To run the server over stdio for local agent processes:
```bash
python -m enhancement.mcp.server
```
To run the server over SSE (Server-Sent Events) for networked clients:
```bash
python -c "from enhancement.mcp.server import mcp_server; mcp_server.run(transport='sse')"
```

### 9.2 Connecting with LangChain MCP Adapters
```python
from enhancement.mcp.client import CAPABLMCPClient

client = CAPABLMCPClient()
langchain_tools = client.get_langchain_tools()
# Pass langchain_tools to create_recruitment_agent() or external orchestrators
```

### 9.3 Live M9 Verification
To verify the complete 15-checkpoint live MCP boundary:
```bash
python scripts/verify_m9_live.py
```
Expected output:
```text
MILESTONE 9 LIVE VERIFICATION RESULT: 15/15 PASSED
>>> ALL 15 CHECKPOINTS PASSED. M9 EXTERNAL MCP BOUNDARY IS VERIFIED & OPERATIONAL. <<<
```
