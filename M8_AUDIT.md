# CAPABL Track 6 — Milestone 8 Production & Deployment Audit

**Project**: Recruitment Intelligence Agent  
**Track**: CAPABL Track 6 — HR / Recruitment  
**Milestone**: M8 — Production Hardening, Security & Deployment Readiness  
**Author**: Senior Production Engineer  
**Status**: AUDIT COMPLETE — BASELINE DOCUMENTED (Pre-Remediation)  
**Date**: 2026-09-25  

---

## 1. Executive Baseline & Verification Status

Prior to Milestone 8, the system completed Milestones M0 through M7 with a verified baseline:
- **Full System Regression**: 167 / 167 tests passing (100% pass rate).
- **Evaluation Baseline Harness**: 30 / 30 cases passing across all 5 evaluation dimensions (Retrieval, RAG, Tools, Agent, Security).
- **Live Runtime Stack**: 9 / 9 live verification scenarios passing against ChatOllama + Qwen 3 8B.
- **Architectural Boundaries Preserved**:
  - Deterministic M3 Match Engine ($matched = R \cap C$, $missing = R \setminus C$) is authoritative with zero hallucinated percentage scores.
  - Consequential scheduling gatekeeper strictly requires `confirmed=True`.
  - Domain isolation among candidate resumes, job descriptions, and HR policy documents is enforced.
  - Append-only JSONL audit trail is operational.

This audit independently inspects the codebase, configurations, deployment manifests, security controls, and operational readiness to identify all vulnerabilities and gaps that must be remediated in Milestone 8.

---

## 2. Production Risks

1. **Absence of Centralized Production Configuration Layer**:
   - Configuration is currently read via ad-hoc `os.getenv()` calls scattered across `capabl_core/llm/provider.py`, `capabl_core/rag/embeddings.py`, `capabl_core/rag/vectorstore.py`, and `capabl_core/ui/app.py`.
   - There is no formal environment classification (`APP_ENV=development|test|production`) with fail-fast validation at startup.
   - In production mode, invalid or missing provider keys (e.g. `GROQ_API_KEY`) are not caught at initialization time, risking runtime failures during user requests.

2. **ChromaDB Multi-Instance Concurrency in Stateful Architecture**:
   - ChromaDB relies on SQLite and local file locks.
   - While `infra/k8s/base/deployment.yaml` correctly sets `replicas: 1`, the architectural diagram in `DEPLOYMENT_KUBERNETES.md` illustrates multiple pods (`agent-app-1` and `agent-app-2`) mounting the same PVC. Multiple writers against SQLite on a network PVC can cause database lock contention or corruption.
   - The deployment blueprint must document this limitation and enforce single-replica StatefulSet or single-writer Deployment topology.

3. **Plaintext Ingress Communication**:
   - `infra/k8s/base/ingress.yaml` defines standard HTTP port 80 routing without TLS termination or HTTPS redirection annotations.
   - In a production recruitment environment handling candidate PII, TLS termination is mandatory.

---

## 3. Deployment Risks

1. **Docker Container Running as Root**:
   - `infra/docker/Dockerfile` does not declare a non-root `USER` (`appuser`). The container process executes as `root`, violating least-privilege container security standards.

2. **Missing `.dockerignore`**:
   - No `.dockerignore` file exists in the repository root or `infra/docker/`.
   - Running `docker build` could inadvertently package sensitive local artifacts into the container image, including `.env`, `.venv`, `.pytest_cache`, `scratch/`, test fixtures, and local database directories (`data/chroma_db/`).

3. **Inappropriate File Copying in Dockerfile**:
   - Line 28 of `infra/docker/Dockerfile` executes `COPY data/ ./data/`. This bundles local developer documents, sample PDFs, and local vector stores into the immutable image layer rather than mounting persistent storage volumes.

4. **Kubernetes Secret Schema Mismatch**:
   - `infra/k8s/base/secret.yaml` specifies `API_KEY: "placeholder-secret-change-in-production"`.
   - The application runtime expects `GROQ_API_KEY`. Pods launched with this secret will not bind the correct environment variable.

5. **Docker Daemon Availability**:
   - Docker CLI 29.2.0 is installed, but the local Docker Desktop daemon is not currently running in this environment (`//./pipe/dockerDesktopLinuxEngine` unavailable). Static container manifest validation and linting must be used if daemon execution is unavailable.

---

## 4. Security Risks

1. **Unvalidated PDF File Uploads & Path Traversal**:
   - In `capabl_core/workflow/service.py` and `capabl_core/ingestion/pdf_loader.py`:
     - Uploaded file names are trusted directly. A filename such as `../../secret.pdf` or `\Windows\System32\cmd.exe` could lead to directory traversal or unsafe temporary file paths.
     - Files are verified only by the `.pdf` extension; there is no magic-byte validation (`%PDF-`) to prevent executable or malformed binary payloads from being processed by PyPDF.
     - Empty (0-byte) files are not rejected before invoking `PyPDFLoader`.

2. **Audit Logger String Redaction Coverage**:
   - `enhancement/security/audit_logger.py` scrubs dictionary keys that match `REDACT_KEYS` (e.g. `password`, `secret`, `api_key`).
   - However, if a user query, freeform recruiter prompt, or LLM response embeds candidate PII (email addresses, phone numbers, SSNs) or bearer tokens within a string payload, the current dictionary-key check does not catch them unless regex content redaction is applied.

3. **Exception Leakage**:
   - Unhandled exceptions in the Streamlit UI or agent execution could leak internal directory paths, stack traces, or environment details to recruiters.

---

## 5. Dependency Risks

1. **Package Declarations & Deprecations**:
   - `requirements.txt` and `pyproject.toml` declare required packages with bounded ranges.
   - `python -m pip check` confirms `No broken requirements found`.
   - `PyPDFLoader` emits a `DeprecationWarning` regarding `langchain-community`. This warning does not break functionality, but migration to standalone integration libraries should be tracked.
   - Need formal `DEPENDENCY_SECURITY.md` recording all packages, versions, and vulnerability statuses.

2. **Package Reproducibility**:
   - Dependencies are constrained with `>=` and `<`. While suitable for libraries, production container deployments require deterministic lockfiles or pinned versions.

---

## 6. Configuration Risks

1. **Scattered Environment Variables**:
   - Environment variables (`LLM_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `GROQ_API_KEY`, `GROQ_MODEL`, `CHROMA_PERSIST_DIRECTORY`, `CHROMA_COLLECTION_NAME`, `EMBEDDING_MODEL_NAME`, `LOG_LEVEL`) are accessed without central type validation or schema enforcement.

2. **Silent Failure Modes**:
   - When an invalid provider string is passed to `create_llm()`, a `ValueError` is raised, but if environment variables are empty or missing, fallback defaults may silently activate rather than alerting the administrator during application startup.

---

## 7. Persistence & Recovery Risks

1. **Chroma Vector Store Integrity**:
   - `ChromaVectorStoreManager` initializes the persistent SQLite database, but does not perform write-read health probes on initialization.
   - If the directory permissions are read-only or the underlying SQLite file is corrupted, the application fails during user ingestion rather than at startup.

2. **Lack of Automated Backup & Restore Utilities**:
   - There are no automated scripts or CLI utilities to create deterministic tarball/compressed snapshots of `./data/chroma_db` and `./data/mock_calendar.json` or to restore them in disaster recovery scenarios.

---

## 8. Resource Risks

1. **Unbounded PDF Upload Size**:
   - No limit is currently enforced on the size of uploaded resume or JD files. An attacker or recruiter could upload a 500MB PDF, leading to memory exhaustion.

2. **Unbounded PDF Page Count**:
   - A multi-thousand-page document would cause PyPDF to block the event loop for minutes and saturate vector store capacity.

3. **Unbounded Chunk Ingestion**:
   - No ceiling exists on the maximum number of chunks a single document can produce.

4. **Unbounded Recruiter Query Length**:
   - Prompts sent to the agent have no length boundaries, allowing potential denial-of-service via huge token contexts.

5. **Audit Log File Growth**:
   - `logs/audit/audit_trail.jsonl` appends indefinitely with no size ceiling, log rotation, or retention policy.

---

## 9. Logging Risks

1. **Disk Saturation via Audit Trail**:
   - Continuous evaluations and high-volume recruiting can bloat `logs/audit/audit_trail.jsonl` to gigabytes if not rotated.

2. **Audit Logger Availability**:
   - If writing to disk fails (e.g. disk full), the logger currently catches and logs a warning. However, critical security events (such as unauthorized booking attempts) must be guaranteed observable.

---

## 10. Recovery Risks

1. **Disaster Recovery Gap**:
   - In the event of disk corruption or accidental deletion of `./data/chroma_db`, there is no documented or automated mechanism to restore the vector store from backup and verify retrieval functionality.

---

## 11. Summary of M8 Action Items

To satisfy the M8 Constitution and achieve production readiness:

| Category | Remediation Scope |
| :--- | :--- |
| **Configuration** | Build `capabl_core/config/production_config.py` with typed Pydantic models, environment validation (`APP_ENV`), and fail-fast startup checks. |
| **Upload Hardening** | Implement `FileValidator` enforcing MIME/magic byte checks (`%PDF-`), size limits (`MAX_UPLOAD_SIZE_MB`), page count limits (`MAX_PDF_PAGES`), and path-traversal-safe filename sanitization. |
| **Resource Limits** | Enforce configurable limits on upload sizes, PDF pages, max chunks, query character length, and LLM timeouts. |
| **PII & Secret Defense** | Add comprehensive regex-based masking in `audit_logger.py` covering email addresses, phone numbers, SSNs, credit cards, bearer tokens, and API keys. |
| **Audit Log Rotation** | Implement safe file rotation and retention limits (e.g. max bytes per log file and backup count) in `RecruitmentAuditLogger`. |
| **Chroma Backup & Restore** | Build deterministic backup and restore utilities (`backup_chroma_db`, `restore_chroma_db`) with automated recovery verification tests. |
| **Health & Readiness** | Implement lightweight `/health/liveness` and `/health/readiness` check functions verifying Chroma, LLM configuration, and storage without expensive LLM generation calls. |
| **Failure Hardening** | Formalize retry policies classifying transient vs non-retryable errors, bounded retries, and graceful degradation states. |
| **Container Hardening** | Update `Dockerfile` to use a non-root user (`appuser`), remove static data copying, add `.dockerignore`, and align `infra/k8s/base/secret.yaml`. |
| **Documentation** | Author `DEPENDENCY_SECURITY.md`, update `DEPLOYMENT.md`, `DEPLOYMENT_KUBERNETES.md`, and `SECURITY.md`. |
| **Automated Testing** | Implement `test_m8_hardening.py`, `test_m8_security.py`, `test_m8_deployment.py`, and master smoke script `scripts/verify_m8_deployment.py`. |
| **Final Verification** | Execute full test regression (167 baseline + M8 new tests), live M7 verification, and produce `M8_VERIFICATION_REPORT.md`. |

---
*Audit completed. Proceeding to systematic implementation of Milestone 8 hardening.*
