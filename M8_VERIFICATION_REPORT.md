# Milestone 8 — Production Hardening & Deployment Verification Report

**Project**: Recruitment Intelligence Agent  
**Track**: CAPABL Track 6 — HR / Recruitment  
**Milestone**: M8 — Production Hardening, Security & Deployment Readiness  
**Evaluation Date**: 2026-09-25  
**Final Verdict**: **PASS**  

---

## 1. M8 Verification Matrix

| Area | Status | Evidence |
|---|---|---|
| **Configuration** | **PASS** | `tests/integration/test_m8_hardening.py::test_01_production_settings_defaults`, `test_02_production_settings_groq_validation`, `test_03_production_settings_masked_representation` (All passed; fail-fast validation and masked repr verified) |
| **Secrets** | **PASS** | Repository scan completed (`git status`, regex secret search). 0 hardcoded API keys/passwords. `tests/security/test_m8_security.py::test_13_redact_bearer_tokens_and_api_keys` passed. |
| **PII** | **PASS** | `tests/security/test_m8_security.py::test_10_redact_candidate_email`, `test_11_redact_candidate_phone`, `test_12_redact_ssn`, `test_14_sanitize_payload_nested_dict` (All passed; candidate emails, phones, SSNs, credit cards scrubbed) |
| **Upload security** | **PASS** | `tests/security/test_m8_security.py::test_01-test_09` (9 tests passed: path traversal unix/windows/etc_passwd, empty file rejection, magic bytes signature `%PDF-`, 10MB file limit, 20-page limit) |
| **Chroma persistence** | **PASS** | `tests/integration/test_m8_hardening.py::test_10_chroma_backup_and_restore_cycle`, single-writer SQLite invariant verified (`replicas: 1`, `strategy: Recreate`) |
| **Backup/restore** | **PASS** | `create_chroma_backup()` and `restore_chroma_backup()` tested end-to-end with tar-slip traversal prevention. Checkpoint 15 of `scripts/verify_m8_deployment.py` passed. |
| **Docker** | **PARTIAL** | Static Dockerfile validation passed (minimal `python:3.10-slim`, non-root user `appuser:10001`, health check, `.dockerignore` coverage verified in `tests/deployment/test_m8_deployment.py::test_01-test_05`). Local Docker engine daemon was not active on Windows host, preventing container runtime spin-up. |
| **Dependencies** | **PASS** | `DEPENDENCY_SECURITY.md` completed. Audited all 16 runtime dependencies (LangChain, Streamlit, ChromaDB, Pydantic, etc.). Zero unused packages, zero unpinned vulnerabilities. |
| **Streamlit** | **PASS** | `tests/deployment/test_m8_deployment.py::test_15_streamlit_app_import_readiness` passed. UI and cached agent imports verified cleanly with zero runtime exceptions. |
| **Health checks** | **PASS** | `tests/deployment/test_m8_deployment.py::test_12_liveness_check_runtime`, `test_13_readiness_check_runtime`, `test_14_readiness_check_degraded_state` passed. Non-LLM readiness probe verified. |
| **Resource limits** | **PASS** | Configured and enforced in `capabl_core/config/settings.py` (`MAX_UPLOAD_SIZE_MB=10`, `MAX_PDF_PAGES=20`, `MAX_DOCUMENT_CHUNKS=100`, `MAX_QUERY_LENGTH=1000`, `LLM_TIMEOUT_SECONDS=60`). Verified in K8s ConfigMap. |
| **Failure handling** | **PASS** | `tests/integration/test_m8_hardening.py::test_06_failure_classification_retryable`, `test_07_failure_classification_non_retryable`, `test_08_bounded_retry_execution`, `test_09_bounded_retry_exhaustion` passed. Bounded exponential backoff verified. |
| **Kubernetes** | **PARTIAL** | Static YAML manifest audit passed (`tests/deployment/test_m8_deployment.py::test_06-test_11`). Deployment `replicas: 1`, non-root `securityContext`, probes, and PVC volume mounts statically verified. Live cluster deployment not executed locally. |
| **Ingress/TLS** | **PARTIAL** | `infra/k8s/base/ingress.yaml` syntax, WebSocket service annotations, and TLS secret references verified in `test_11_k8s_ingress_tls_and_websockets`. Production certificate issuer (Let's Encrypt) verified structurally. |
| **Audit logging** | **PASS** | `tests/security/test_m8_security.py::test_15_audit_logger_rotation_on_size_limit` passed. Append-only structured JSONL logging with UTC timestamps, duration_ms, and size rotation verified. |
| **Security suite** | **PASS** | `tests/security/test_m8_security.py` (16/16 tests passed). Covers input validation, prompt injection defense, candidate domain isolation, and booking gatekeeper. |
| **Deployment smoke test**| **PASS** | `scripts/verify_m8_deployment.py` (15/15 checkpoints passed). Full stack smoke verification against live ChatOllama + Qwen 3 8B. |
| **Full regression** | **PASS** | `python -m pytest tests/ -v` (208 passed, 0 failed, 1 warning in 147.36s). |

---

## 2. Regression & Verification Evidence Summary

### 2.1 Pytest Suite Execution
- **Command**: `python -m pytest tests/ -v`
- **Total Tests**: 208
- **Passed**: 208 (100.0%)
- **Failed**: 0 (0.0%)
- **Duration**: 147.36 seconds
- **Breakdown**:
  - `tests/unit/`: 105 tests passed
  - `tests/integration/`: 41 tests passed (including 10 M8 hardening tests)
  - `tests/evaluation/`: 31 tests passed
  - `tests/security/`: 16 tests passed (16 dedicated M8 security tests)
  - `tests/deployment/`: 15 tests passed (15 dedicated M8 deployment tests)

### 2.2 Milestone 7 Live Runtime Verification
- **Command**: `python scripts/verify_m7_live.py`
- **Live Scenarios**: 9/9 PASSED (100.0%)
- **Provider**: ChatOllama + Qwen 3 8B
- **Verification Elements**:
  1. Real UI & Dashboard Import: **PASS**
  2. Real PDF Ingestion & Domain Isolation: **PASS**
  3. Proactive Deterministic Match Workflow (Zero Percentages): **PASS**
  4. Recruiter Follow-Up with Active Match Context: **PASS**
  5. Cross-Candidate & Cross-Domain Isolation: **PASS**
  6. Dedicated Policy Evidence Tool Execution: **PASS**
  7. Calendar Gatekeeper Unconfirmed Booking Block: **PASS**
  8. Calendar Confirmed Booking Execution: **PASS**
  9. Observability & Audit Trail Integrity: **PASS**

### 2.3 Milestone 8 Master Deployment Smoke Verification
- **Command**: `python scripts/verify_m8_deployment.py`
- **Checkpoints**: 15/15 PASSED (100.0%)
- **Checkpoints Verified**:
  1. Application Imports: **PASS**
  2. Configuration & Environment Hardening: **PASS**
  3. LLM Provider Contract: **PASS**
  4. Application Health & Readiness Probes: **PASS**
  5. Chroma Persistence Initialization: **PASS**
  6. Hardened PDF Ingestion: **PASS**
  7. Domain Metadata Isolation: **PASS**
  8. Deterministic M3 Matching Engine: **PASS**
  9. Evidence Retrieval Service: **PASS**
  10. Agent Initialization & ReAct Execution: **PASS**
  11. Interview Slot Search: **PASS**
  12. Calendar Gatekeeper Unconfirmed Blocking: **PASS**
  13. Calendar Confirmed Booking: **PASS**
  14. Audit Logging & PII Scrubbing: **PASS**
  15. Chroma Persistence Backup & Restore Cycle: **PASS**

---

## 3. Known Limitations & Production Notes

1. **Docker Daemon Availability**:
   - The Windows host has Docker CLI v29.2.0 installed, but the Docker Desktop daemon was not running during evaluation. Dockerfile and `.dockerignore` were validated statically via `test_m8_deployment.py`.
2. **Kubernetes Environment**:
   - Kubernetes manifests (`infra/k8s/base/`) were validated statically and syntactically. Multi-pod scaling must never exceed `replicas: 1` due to ChromaDB SQLite single-writer persistence requirements unless an external vector service is provisioned.
3. **Groq Provider Cloud Requirement**:
   - When deploying to public clouds without local GPU inference, `LLM_PROVIDER=groq` must be set in conjunction with a valid `GROQ_API_KEY`. In production mode (`APP_ENV=production`), missing keys fail fast at startup without silent fallback.
