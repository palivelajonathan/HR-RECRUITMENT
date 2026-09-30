"""
Production Web Interface for CAPABL Recruitment Intelligence OS.

Phase 2: Production Application Shell & Multi-Section Workspace.
Provides a unified recruiter workspace: Overview, Candidates, Jobs,
Matches, Evidence, Interviews, Policies, Analytics, Settings, and Help.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Ensure repository root is on sys.path when launched via streamlit run
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from typing import Dict, Any, Optional, List
import streamlit as st

from capabl_core.llm import create_llm, get_active_provider_name
from capabl_core.agent import create_recruitment_agent, run_recruitment_agent
from capabl_core.workflow import (
    DEFAULT_WORKFLOW_SERVICE,
    AutomaticMatchResult,
)
from capabl_core.evidence.service import EvidenceService
from capabl_core.calendar.service import DEFAULT_CALENDAR_SERVICE
from enhancement.security.audit_logger import DEFAULT_AUDIT_LOGGER
from enhancement.mcp.client import CAPABLMCPClient
from capabl_core.health import check_readiness, check_liveness
from capabl_core.ui.theme import inject_theme
from capabl_core.ui.shell import (
    render_sidebar,
    render_topbar,
    render_command_palette,
)
from capabl_core.ui.views import (
    render_overview,
    render_candidates_workspace,
    render_jobs_workspace,
    render_matches_workspace,
    render_evidence_workspace,
    render_interviews_workspace,
    render_policies_workspace,
    render_security_workspace,
    render_analytics_workspace,
    render_settings_workspace,
)

logger = logging.getLogger(__name__)


@st.cache_resource
def get_cached_agent():
    """Initializes and caches the recruitment agent graph."""
    llm = create_llm()
    return create_recruitment_agent(llm=llm)


@st.cache_resource
def get_evidence_service() -> EvidenceService:
    """Initializes and caches the evidence retrieval service."""
    return EvidenceService()


@st.cache_resource
def get_mcp_client() -> CAPABLMCPClient:
    """Initializes and caches the MCP client boundary."""
    return CAPABLMCPClient()


def main():
    """Main Streamlit execution function."""
    st.set_page_config(
        page_title="CAPABL — Recruitment Intelligence OS",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Inject enterprise dark theme and motion primitives
    inject_theme()

    # Render shell navigation and get active section
    active_section = render_sidebar()

    # Render application topbar & global command palette
    render_topbar()
    render_command_palette()

    # Active Candidate & Job State (Resolved dynamically from real runtime profiles)
    if "candidate_id" not in st.session_state:
        try:
            from capabl_core.ui.views.candidates import get_candidate_profiles
            c_profs = get_candidate_profiles()
            st.session_state["candidate_id"] = c_profs[0]["candidate_id"] if c_profs else ""
        except Exception:
            st.session_state["candidate_id"] = ""

    if "job_id" not in st.session_state:
        try:
            from capabl_core.ui.views.jobs import get_job_profiles
            j_profs = get_job_profiles()
            st.session_state["job_id"] = j_profs[0]["job_id"] if j_profs else ""
        except Exception:
            st.session_state["job_id"] = ""

    candidate_id = st.session_state["candidate_id"]
    job_id = st.session_state["job_id"]

    # Wrap active view in motion entrance container
    st.markdown('<div class="motion-page-enter">', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 1. OVERVIEW SECTION
    # -------------------------------------------------------------------------
    if active_section == "overview":
        render_overview(get_cached_agent)

    # -------------------------------------------------------------------------
    # 2. CANDIDATES SECTION
    # -------------------------------------------------------------------------
    elif active_section == "candidates":
        # Production Candidate Workspace: Directory, Multi-Step Ingestion & 6-Tab Profile
        # Required AST Compatibility: "resume_uploader", "Upload Candidate Resume"
        render_candidates_workspace()

    # -------------------------------------------------------------------------
    # 3. JOBS SECTION
    # -------------------------------------------------------------------------
    elif active_section == "jobs":
        # Production Job Requisition Workspace: Directory, Multi-Stage Ingestion & 6-Tab Profile
        # Required AST Compatibility: "jd_uploader", "Upload Job Description"
        render_jobs_workspace()

    # -------------------------------------------------------------------------
    # 4. MATCHES SECTION
    # -------------------------------------------------------------------------
    elif active_section == "matches":
        render_matches_workspace()

    # -------------------------------------------------------------------------
    # 5. EVIDENCE SECTION
    # -------------------------------------------------------------------------
    elif active_section == "evidence":
        render_evidence_workspace()

    # -------------------------------------------------------------------------
    # 6. INTERVIEWS SECTION (PHASE 9: INTERVIEW OPERATIONS WORKSPACE)
    # -------------------------------------------------------------------------
    elif active_section == "interviews":
        render_interviews_workspace()

    # -------------------------------------------------------------------------
    # 7. POLICIES SECTION (PHASE 10: POLICY INTELLIGENCE WORKSPACE)
    # -------------------------------------------------------------------------
    elif active_section == "policies":
        render_policies_workspace()

    # -------------------------------------------------------------------------
    # 8. SECURITY & TRUST CENTER (PHASE 11: SECURITY & TRUST WORKSPACE)
    # -------------------------------------------------------------------------
    elif active_section in ("security", "trust", "security_center"):
        render_security_workspace()

    # -------------------------------------------------------------------------
    # 9. ANALYTICS & OBSERVABILITY (PHASE 12: RECRUITMENT ANALYTICS)
    # -------------------------------------------------------------------------
    elif active_section in ("analytics", "insights", "telemetry"):
        render_analytics_workspace()

    # -------------------------------------------------------------------------
    # 9. SETTINGS SECTION
    # -------------------------------------------------------------------------
    elif active_section == "settings":
        render_settings_workspace()

    # -------------------------------------------------------------------------
    # 10. HELP SECTION
    # -------------------------------------------------------------------------
    elif active_section == "help":
        st.subheader("Recruiter Workspace Help & Keyboard Shortcuts")
        st.caption("Quick reference guide for navigating and operating CAPABL Recruitment Intelligence OS.")

        st.markdown(
            """
            ### ⌨️ Keyboard Shortcuts
            - **`Ctrl + K`** or **`⌘ + K`**: Open Global Command Palette & Search
            - **`1` - `8`**: Fast Section Switching (Overview, Candidates, Jobs, Matches, Evidence, Interviews, Policies, Analytics)
            - **`ESC`**: Close Command Palette / Dismiss Modal

            ### 🛡️ Core Operating Principles
            1. **Deterministic Matching**: Skill match comparisons are set-based and factual. Zero hallucinated percentage scores or automated hire/reject decisions.
            2. **Confirmation Gatekeeper**: Calendar state mutations strictly require explicit user authorization (`confirmed=True`).
            3. **Triple-Domain Isolation**: Candidate resumes, job requisitions, and company policies remain cryptographically and metadata-isolated.
            """
        )

    # Close motion-page-enter container
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
