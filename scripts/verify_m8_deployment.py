"""
scripts/verify_m8_deployment.py

Milestone 8 Master Deployment & Production Hardening Smoke Verification Script.

Executes all 15 required deployment checkpoints:
1. Application imports cleanly (UI, Agent, Workflow, Health, Config)
2. Production configuration loads with valid settings & boundaries
3. Provider configuration is valid (Ollama / Groq contract)
4. Application Health Liveness & Readiness checks return healthy
5. Chroma persistent vector store initializes cleanly
6. Sample PDF ingestion with hardening & size validation works
7. Domain metadata isolation is strictly enforced
8. Deterministic M3 matching works (set-based, zero percentages)
9. Evidence retrieval works (candidate, JD, policy isolation)
10. Agent initializes and executes ReAct flow
11. Calendar interview slot search works
12. Unconfirmed booking is blocked by gatekeeper (confirmed=False)
13. Confirmed booking succeeds (confirmed=True)
14. Audit logging writes structured JSONL with PII/secret scrubbing
15. Chroma deterministic backup and restore procedure succeeds
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Ensure workspace root is in python path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_m8_deployment_smoke_test() -> bool:
    print("=" * 80)
    print("       CAPABL TRACK 6 -- MILESTONE 8 PRODUCTION DEPLOYMENT SMOKE TEST")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Workspace: {WORKSPACE_ROOT}")

    passed_checkpoints = 0
    total_checkpoints = 15

    # -------------------------------------------------------------------------
    # CHECKPOINT 1: Application Imports
    # -------------------------------------------------------------------------
    print("\n--- [CHECKPOINT 1/15] Application Imports ---")
    try:
        from capabl_core.config.settings import get_settings, ProductionSettings
        from capabl_core.health.checks import check_liveness, check_readiness
        from capabl_core.llm import create_llm, get_active_provider_name
        from capabl_core.rag.vectorstore import ChromaVectorStoreManager
        from capabl_core.rag.retriever import RecruitmentRetriever
        from capabl_core.rag.persistence import create_chroma_backup, restore_chroma_backup, verify_chroma_storage_integrity
        from capabl_core.ingestion.validator import sanitize_filename, validate_pdf_content
        from capabl_core.workflow.service import AutomaticMatchService
        from capabl_core.workflow.models import AutomaticMatchResult
        from capabl_core.agent import create_recruitment_agent, run_recruitment_agent
        from capabl_core.evidence.service import EvidenceService
        from capabl_core.tools.policy_tool import create_policy_evidence_tool
        from capabl_core.tools.calendar_tool import search_interview_slots, book_interview
        from enhancement.security.audit_logger import RecruitmentAuditLogger, sanitize_payload
        from capabl_core.ui.app import main, get_cached_agent

        print("[PASS] All core modules, UI entrypoints, and health subsystems imported cleanly.")
        passed_checkpoints += 1
    except Exception as exc:
        print(f"[FAIL] Module import failed: {exc}")
        return False

    # -------------------------------------------------------------------------
    # CHECKPOINT 2: Configuration & Environment Hardening
    # -------------------------------------------------------------------------
    print("\n--- [CHECKPOINT 2/15] Configuration & Environment Hardening ---")
    try:
        cfg = get_settings()
        assert cfg.app_env is not None, "app_env must be defined"
        assert cfg.max_upload_size_mb > 0, "max_upload_size_mb must be > 0"
        assert cfg.max_pdf_pages > 0, "max_pdf_pages must be > 0"
        assert cfg.max_document_chunks > 0, "max_document_chunks must be > 0"
        assert cfg.max_query_length > 0, "max_query_length must be > 0"
        assert cfg.llm_timeout_seconds > 0, "llm_timeout_seconds must be > 0"

        # Verify masked representation prevents accidental secret leaks in repr
        cfg_repr = repr(cfg)
        if cfg.groq_api_key:
            assert cfg.groq_api_key not in cfg_repr, "Raw GROQ_API_KEY must not appear in repr(settings)"

        print(f"[PASS] Configuration loaded. App Env: {cfg.app_env.value}, LLM Provider: {cfg.llm_provider}")
        passed_checkpoints += 1
    except Exception as exc:
        print(f"[FAIL] Configuration verification failed: {exc}")
        return False

    # -------------------------------------------------------------------------
    # CHECKPOINT 3: LLM Provider Contract
    # -------------------------------------------------------------------------
    print("\n--- [CHECKPOINT 3/15] LLM Provider Contract ---")
    try:
        active_provider = get_active_provider_name()
        print(f"Active Provider: {active_provider}")
        llm = create_llm()
        assert llm is not None, "LLM instance must be created"
        print(f"[PASS] Provider contract valid for {active_provider}.")
        passed_checkpoints += 1
    except Exception as exc:
        print(f"[FAIL] Provider contract check failed: {exc}")
        return False

    # -------------------------------------------------------------------------
    # CHECKPOINT 4: Health Liveness & Readiness Probes
    # -------------------------------------------------------------------------
    print("\n--- [CHECKPOINT 4/15] Application Health & Readiness Probes ---")
    try:
        liveness = check_liveness()
        assert liveness.get("alive") is True, "Liveness probe must report alive=True"
        assert liveness.get("status") == "healthy", "Liveness status must be 'healthy'"

        readiness = check_readiness()
        assert "checks" in readiness, "Readiness must return subsystem checks"
        assert readiness["checks"]["config"]["status"] == "pass", "Config check must pass"
        assert readiness["checks"]["filesystem"]["status"] == "pass", "Filesystem check must pass"

        print(f"[PASS] Liveness probe: {liveness['status']}, Readiness status: {readiness['status']}.")
        passed_checkpoints += 1
    except Exception as exc:
        print(f"[FAIL] Health probes failed: {exc}")
        return False

    # -------------------------------------------------------------------------
    # Setup Sandbox Directory for Ingestion, VectorStore & Audit
    # -------------------------------------------------------------------------
    sandbox_dir = tempfile.mkdtemp(prefix="capabl_m8_smoke_")
    sandbox_path = Path(sandbox_dir)

    try:
        # ---------------------------------------------------------------------
        # CHECKPOINT 5: Chroma Persistence Initialization
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 5/15] Chroma Persistence Initialization ---")
        chroma_dir = sandbox_path / "chroma_db"
        chroma_dir.mkdir(parents=True, exist_ok=True)
        vstore_mgr = ChromaVectorStoreManager(
            persist_directory=str(chroma_dir),
            collection_name="m8_smoke_test_collection",
        )
        store = vstore_mgr.get_or_create_store()
        assert store is not None, "Chroma vector store must be initialized"
        print(f"[PASS] Chroma initialized at {chroma_dir} with collection '{vstore_mgr.collection_name}'.")
        passed_checkpoints += 1

        # ---------------------------------------------------------------------
        # CHECKPOINT 6: Hardened PDF Ingestion
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 6/15] Hardened PDF Ingestion ---")
        retriever = RecruitmentRetriever(vectorstore_or_manager=vstore_mgr)
        service = AutomaticMatchService(vectorstore_manager=vstore_mgr, retriever=retriever)

        sample_dir = WORKSPACE_ROOT / "data" / "sample"
        alex_pdf = sample_dir / "resumes" / "resume_alex_chen.pdf"
        jd_pdf = sample_dir / "job_descriptions" / "jd_senior_backend_lead.pdf"
        policy_pdf = sample_dir / "policies" / "policy_leave_and_attendance.pdf"

        assert alex_pdf.exists(), f"Sample resume missing: {alex_pdf}"
        assert jd_pdf.exists(), f"Sample JD missing: {jd_pdf}"
        assert policy_pdf.exists(), f"Sample policy missing: {policy_pdf}"

        # Test malicious path sanitization
        malicious_name = "../../../etc/passwd.pdf"
        sanitized = sanitize_filename(malicious_name)
        assert "/" not in sanitized and ".." not in sanitized, f"Sanitization failed: {sanitized}"

        alex_chunks = service.ingest_document(
            file_path_or_bytes=alex_pdf,
            document_type="resume",
            document_id="alex_chen",
            candidate_id="alex_chen",
            filename=alex_pdf.name,
        )
        assert alex_chunks > 0, "Alex Chen resume chunks must be > 0"

        jd_chunks = service.ingest_document(
            file_path_or_bytes=jd_pdf,
            document_type="job_description",
            document_id="jd_backend_lead",
            job_id="jd_backend_lead",
            filename=jd_pdf.name,
        )
        assert jd_chunks > 0, "JD chunks must be > 0"

        policy_chunks = service.ingest_document(
            file_path_or_bytes=policy_pdf,
            document_type="policy",
            document_id="policy_leave",
            filename=policy_pdf.name,
        )
        assert policy_chunks > 0, "Policy chunks must be > 0"

        print(f"[PASS] PDF Ingestion: Resume ({alex_chunks} chunks), JD ({jd_chunks} chunks), Policy ({policy_chunks} chunks).")
        passed_checkpoints += 1

        # ---------------------------------------------------------------------
        # CHECKPOINT 7: Domain Metadata Isolation
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 7/15] Domain Metadata Isolation ---")
        resume_docs = retriever.retrieve_candidate_evidence(candidate_id="alex_chen", query="leave policy PTO attendance", top_k=5)
        for doc in resume_docs:
            assert doc.metadata.get("document_type") == "resume", f"Non-resume leaked into candidate retrieval: {doc.metadata}"
            assert doc.metadata.get("candidate_id") == "alex_chen", f"Wrong candidate: {doc.metadata}"

        policy_docs = retriever.retrieve_policy_evidence(query="Python FastAPI distributed systems", top_k=5)
        for doc in policy_docs:
            assert doc.metadata.get("document_type") == "policy", f"Non-policy leaked into policy retrieval: {doc.metadata}"

        print("[PASS] Candidate and Policy domains are strictly isolated in vector retrieval.")
        passed_checkpoints += 1

        # ---------------------------------------------------------------------
        # CHECKPOINT 8: Deterministic M3 Matching Engine
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 8/15] Deterministic M3 Matching Engine ---")
        match_res = service.run_automatic_match(
            candidate_id="alex_chen",
            job_id="jd_backend_lead",
            trigger="automatic",
        )
        assert match_res.status == "match_ready", f"Expected match_ready, got {match_res.status}"
        assert match_res.match_result is not None, "Match result is None"
        matched_skills = match_res.match_result.matched_skills
        missing_skills = match_res.match_result.missing_skills
        assert len(matched_skills) > 0, "Must have matched skills"

        # Verify mathematical set invariants: Matched intersect Missing == empty
        intersect = set(matched_skills).intersection(set(missing_skills))
        assert len(intersect) == 0, f"Invariant violation: matched & missing overlap: {intersect}"

        print(f"[PASS] Deterministic matching verified: {len(matched_skills)} matched, {len(missing_skills)} missing. Set isolation preserved.")
        passed_checkpoints += 1

        # ---------------------------------------------------------------------
        # CHECKPOINT 9: Evidence Retrieval Service
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 9/15] Evidence Retrieval Service ---")
        evidence_service = EvidenceService(retriever=retriever)
        candidate_env = evidence_service.get_candidate_evidence(query="Python experience", candidate_id="alex_chen", top_k=3)
        assert candidate_env.document_type == "resume"
        assert len(candidate_env.items) > 0
        assert all(item.candidate_id == "alex_chen" for item in candidate_env.items)
        assert all(item.document_type == "resume" for item in candidate_env.items)

        policy_env = evidence_service.get_policy_evidence(query="sick leave probation policy", top_k=3)
        assert policy_env.document_type == "policy"
        assert len(policy_env.items) > 0
        assert all(item.document_type == "policy" for item in policy_env.items)

        print("[PASS] Structured evidence envelopes with domain boundary metadata verified.")
        passed_checkpoints += 1

        # ---------------------------------------------------------------------
        # CHECKPOINT 10: Agent Initialization & ReAct Flow
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 10/15] Agent Initialization & Execution ---")
        agent_executor = create_recruitment_agent(llm=llm)
        assert agent_executor is not None, "Agent executor must initialize"

        test_query = "What skills are missing for candidate Alex Chen?"
        agent_res = run_recruitment_agent(
            agent=agent_executor,
            query=test_query,
            match_context=match_res,
            session_id="m8_smoke_agent",
        )
        assert agent_res.status == "success", f"Agent execution failed with status {agent_res.status}"
        assert len(agent_res.answer) > 0, "Agent must return non-empty answer"
        print(f"[PASS] Agent successfully executed query and generated answer ({len(agent_res.answer)} chars).")
        passed_checkpoints += 1

        # ---------------------------------------------------------------------
        # CHECKPOINT 11: Interview Slot Search
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 11/15] Interview Slot Search ---")
        search_output = search_interview_slots.invoke({"role_type": "technical", "preferred_date": "2026-10-01"})
        assert "available" in str(search_output).lower() or "slot" in str(search_output).lower()
        print("[PASS] Calendar search returned available interview slots.")
        passed_checkpoints += 1

        # ---------------------------------------------------------------------
        # CHECKPOINT 12: Calendar Gatekeeper (Unconfirmed Blocking)
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 12/15] Calendar Gatekeeper (Unconfirmed Blocking) ---")
        blocked_res = book_interview.invoke({
            "slot_id": "slot_001",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "confirmed": False,
        })
        assert blocked_res.get("status") == "confirmation_required", f"Gatekeeper failed to block unconfirmed booking: {blocked_res}"
        assert blocked_res.get("booking") is None
        print(f"[PASS] Gatekeeper strictly blocked unconfirmed booking (status='confirmation_required').")
        passed_checkpoints += 1

        # ---------------------------------------------------------------------
        # CHECKPOINT 13: Calendar Confirmed Booking
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 13/15] Calendar Confirmed Booking ---")
        confirmed_res = book_interview.invoke({
            "slot_id": "slot_001",
            "candidate_id": "alex_chen",
            "job_id": "jd_backend_lead_2026",
            "confirmed": True,
        })
        assert confirmed_res.get("status") in ("confirmed", "success"), f"Confirmed booking failed: {confirmed_res}"
        assert confirmed_res.get("booking") is not None
        print(f"[PASS] Confirmed booking executed successfully: booking_id={confirmed_res.get('booking', {}).get('booking_id')}")
        passed_checkpoints += 1

        # ---------------------------------------------------------------------
        # CHECKPOINT 14: Audit Logging & PII Scrubbing
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 14/15] Audit Logging & PII Scrubbing ---")
        audit_file = sandbox_path / "audit_trail.jsonl"
        audit_logger = RecruitmentAuditLogger(
            log_directory=str(sandbox_path),
            log_file_path=str(audit_file),
            max_bytes=1024 * 1024,
            backup_count=3,
        )

        test_payload = {
            "candidate_name": "Alex Chen",
            "email": "alex.chen@example.org",
            "phone": "415-555-9876",
            "ssn": "000-11-2222",
            "groq_api_key": "gsk_prod_live_secret_key_1234567890",
        }
        event = audit_logger.log_event("candidate_screened", payload=test_payload)

        # Inspect logged content on disk
        with open(audit_file, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
        assert len(log_lines) > 0, "Audit log file must contain record"
        raw_log_entry = log_lines[-1]

        assert "alex.chen@example.org" not in raw_log_entry, "Email leaked in audit log"
        assert "415-555-9876" not in raw_log_entry, "Phone number leaked in audit log"
        assert "000-11-2222" not in raw_log_entry, "SSN leaked in audit log"
        assert "gsk_prod_live_secret_key_1234567890" not in raw_log_entry, "API key leaked in audit log"
        assert "[REDACTED_SECRET]" in raw_log_entry or "[REDACTED_EMAIL]" in raw_log_entry

        print("[PASS] Audit logger successfully scrubbed candidate PII, SSN, and credentials.")
        passed_checkpoints += 1

        # ---------------------------------------------------------------------
        # CHECKPOINT 15: Chroma Persistence Backup & Restore Cycle
        # ---------------------------------------------------------------------
        print("\n--- [CHECKPOINT 15/15] Chroma Persistence Backup & Restore Cycle ---")
        backup_dest = sandbox_path / "chroma_backup.tar.gz"
        backup_path = create_chroma_backup(str(chroma_dir), str(backup_dest))
        assert Path(backup_path).exists(), f"Backup file not created: {backup_path}"

        restore_dir = sandbox_path / "chroma_restored"
        restore_path = restore_chroma_backup(backup_path, str(restore_dir))
        assert Path(restore_path).exists(), f"Restore directory missing: {restore_path}"

        # Verify integrity of restored vector store
        restored_mgr = ChromaVectorStoreManager(
            persist_directory=str(restore_dir),
            collection_name="m8_smoke_test_collection",
        )
        assert restored_mgr.get_or_create_store() is not None
        restored_retriever = RecruitmentRetriever(vectorstore_or_manager=restored_mgr)
        restored_docs = restored_retriever.retrieve_candidate_evidence(candidate_id="alex_chen", query="Python", top_k=2)
        assert len(restored_docs) > 0, "Restored Chroma store must retrieve previously ingested candidate docs"

        print(f"[PASS] Chroma backup, restore, and reload cycle verified. Ingestion survived persistence cycle.")
        passed_checkpoints += 1

    finally:
        # Cleanup temporary sandbox directory
        try:
            shutil.rmtree(sandbox_dir, ignore_errors=True)
        except Exception:
            pass

    print("\n" + "=" * 80)
    print(f"DEPLOYMENT SMOKE TEST RESULT: {passed_checkpoints}/{total_checkpoints} CHECKPOINTS PASSED")
    print("=" * 80)

    if passed_checkpoints == total_checkpoints:
        print("[SUCCESS] ALL 15 DEPLOYMENT CHECKPOINTS PASSED. SYSTEM IS DEPLOYMENT & PRODUCTION READY.")
        return True
    else:
        print("[FAILURE] Some checkpoints failed. Review logs above.")
        return False


if __name__ == "__main__":
    success = run_m8_deployment_smoke_test()
    sys.exit(0 if success else 1)
