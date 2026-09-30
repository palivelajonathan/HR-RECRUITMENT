"""
Automatic Resume + JD Match Workflow Module.
"""

from capabl_core.workflow.models import (
    WorkflowStatus,
    WorkflowContext,
    AutomaticMatchResult,
    format_match_summary_markdown,
)
from capabl_core.workflow.service import (
    AutomaticMatchService,
    DEFAULT_WORKFLOW_SERVICE,
    run_automatic_match,
)

__all__ = [
    "WorkflowStatus",
    "WorkflowContext",
    "AutomaticMatchResult",
    "format_match_summary_markdown",
    "AutomaticMatchService",
    "DEFAULT_WORKFLOW_SERVICE",
    "run_automatic_match",
]
