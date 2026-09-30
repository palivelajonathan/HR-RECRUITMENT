"""
CAPABL UI Views Package.

Phase 3: Production Overview & Multi-Section Views.
"""

from capabl_core.ui.views.overview import render_overview, get_workspace_state
from capabl_core.ui.views.candidates import render_candidates_workspace, get_candidate_profiles
from capabl_core.ui.views.jobs import render_jobs_workspace, get_job_profiles
from capabl_core.ui.views.matches import render_matches_workspace
from capabl_core.ui.views.evidence import render_evidence_workspace
from capabl_core.ui.views.agent_workspace import render_agent_workspace
from capabl_core.ui.views.interviews import render_interviews_workspace
from capabl_core.ui.views.policies import render_policies_workspace, get_policy_catalog
from capabl_core.ui.views.security import render_security_workspace
from capabl_core.ui.views.analytics import render_analytics_workspace
from capabl_core.ui.views.settings import render_settings_workspace

__all__ = [
    "render_overview",
    "get_workspace_state",
    "render_candidates_workspace",
    "get_candidate_profiles",
    "render_jobs_workspace",
    "get_job_profiles",
    "render_matches_workspace",
    "render_evidence_workspace",
    "render_agent_workspace",
    "render_interviews_workspace",
    "render_policies_workspace",
    "get_policy_catalog",
    "render_security_workspace",
    "render_analytics_workspace",
    "render_settings_workspace",
]

