"""
Demo Helper Utilities for Milestone 10: Final Product Integration & Demo Readiness.

Provides deterministic demo data loading, state reset, and sample document management
without destroying unrelated persistent Chroma vector store collections.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from capabl_core.workflow import (
    DEFAULT_WORKFLOW_SERVICE,
    AutomaticMatchResult,
)
from capabl_core.calendar.service import DEFAULT_CALENDAR_SERVICE
from enhancement.security.audit_logger import DEFAULT_AUDIT_LOGGER

logger = logging.getLogger(__name__)

SAMPLE_DIR = Path("./data/sample")
SAMPLE_RESUME_ALEX = SAMPLE_DIR / "resumes" / "resume_alex_chen.pdf"
SAMPLE_RESUME_PRIYA = SAMPLE_DIR / "resumes" / "resume_priya_sharma.pdf"
SAMPLE_JD_BACKEND = SAMPLE_DIR / "job_descriptions" / "jd_senior_backend_lead.pdf"
SAMPLE_POLICY_LEAVE = SAMPLE_DIR / "policies" / "policy_leave_and_attendance.pdf"


def get_demo_documents_status() -> Dict[str, bool]:
    """Checks availability of synthetic demo PDF documents on disk."""
    return {
        "alex_chen_resume": SAMPLE_RESUME_ALEX.exists(),
        "priya_sharma_resume": SAMPLE_RESUME_PRIYA.exists(),
        "backend_lead_jd": SAMPLE_JD_BACKEND.exists(),
        "leave_policy": SAMPLE_POLICY_LEAVE.exists(),
    }


def load_demo_candidate(
    candidate: str = "alex_chen",
    job_id: str = "jd_backend_lead_2026",
) -> Dict[str, Any]:
    """
    Deterministically ingests sample candidate resume, job description,
    and policy documents, triggering an immediate automatic match.
    
    Args:
        candidate: Candidate key ('alex_chen' or 'priya_sharma').
        job_id: Target job description identifier.
        
    Returns:
        Dict containing ingestion counts, candidate ID, job ID, and match result.
    """
    clean_candidate = candidate.strip().lower()
    if clean_candidate in ("alex", "alex_chen", "cand_alex_chen"):
        resume_path = SAMPLE_RESUME_ALEX
        actual_cid = "alex_chen"
    elif clean_candidate in ("priya", "priya_sharma", "cand_priya_sharma"):
        resume_path = SAMPLE_RESUME_PRIYA
        actual_cid = "priya_sharma"
    else:
        raise ValueError(f"Unknown demo candidate '{candidate}'. Must be 'alex_chen' or 'priya_sharma'.")

    if not resume_path.exists():
        raise FileNotFoundError(f"Sample resume file missing at: {resume_path}")
    if not SAMPLE_JD_BACKEND.exists():
        raise FileNotFoundError(f"Sample JD file missing at: {SAMPLE_JD_BACKEND}")

    logger.info(f"Loading demo dataset for candidate '{actual_cid}' and job '{job_id}'...")

    # 1. Ingest Resume
    resume_chunks = DEFAULT_WORKFLOW_SERVICE.ingest_document(
        file_path_or_bytes=str(resume_path),
        filename=resume_path.name,
        document_type="resume",
        document_id=actual_cid,
        candidate_id=actual_cid,
        replace=True,
    )

    # 2. Ingest Job Description
    jd_chunks = DEFAULT_WORKFLOW_SERVICE.ingest_document(
        file_path_or_bytes=str(SAMPLE_JD_BACKEND),
        filename=SAMPLE_JD_BACKEND.name,
        document_type="job_description",
        document_id=job_id,
        job_id=job_id,
        replace=True,
    )

    # 3. Ingest Policy if available
    policy_chunks = 0
    if SAMPLE_POLICY_LEAVE.exists():
        policy_chunks = DEFAULT_WORKFLOW_SERVICE.ingest_document(
            file_path_or_bytes=str(SAMPLE_POLICY_LEAVE),
            filename=SAMPLE_POLICY_LEAVE.name,
            document_type="policy",
            document_id="policy_leave_attendance",
            replace=True,
        )

    # 4. Trigger Automatic Match
    match_result: AutomaticMatchResult = DEFAULT_WORKFLOW_SERVICE.run_automatic_match(
        candidate_id=actual_cid,
        job_id=job_id,
        trigger="demo_loader",
    )

    # 5. Audit Log
    DEFAULT_AUDIT_LOGGER.log_event(
        event="demo_loaded",
        status="success",
        payload={
            "candidate_id": actual_cid,
            "job_id": job_id,
            "resume_chunks": resume_chunks,
            "jd_chunks": jd_chunks,
            "policy_chunks": policy_chunks,
            "match_status": match_result.status,
        },
    )

    return {
        "status": "success",
        "candidate_id": actual_cid,
        "job_id": job_id,
        "resume_chunks": resume_chunks,
        "jd_chunks": jd_chunks,
        "policy_chunks": policy_chunks,
        "match_result": match_result,
    }


def reset_demo_state() -> Dict[str, Any]:
    """
    Safely resets demo calendar bookings back to seeded initial availability
    and logs an audit trail event. Does NOT destroy unrelated Chroma data.
    """
    logger.info("Resetting demo calendar state...")
    DEFAULT_CALENDAR_SERVICE.reset()

    DEFAULT_AUDIT_LOGGER.log_event(
        event="demo_reset",
        status="success",
        payload={"message": "Demo calendar bookings reset to initial available slots."},
    )

    return {
        "status": "success",
        "message": "Demo calendar reset successfully. All demo bookings cleared.",
    }
