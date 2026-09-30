"""
CAPABL Production Recruitment Analytics Package.

Phase 12: Recruitment Analytics.
Aggregates and visualizes actual persisted and runtime data:
- Candidates processed
- Roles created
- Matches generated
- Interviews scheduled
- Processing activity
- System activity

Enforces strict data integrity: never fabricates metrics, displays
'Not enough data yet.' when data is insufficient.
"""

from capabl_core.analytics.engine import (
    AnalyticsSnapshot,
    get_analytics_snapshot,
    get_candidates_analytics,
    get_roles_analytics,
    get_matches_analytics,
    get_interviews_analytics,
    get_processing_analytics,
    get_system_analytics,
)

__all__ = [
    "AnalyticsSnapshot",
    "get_analytics_snapshot",
    "get_candidates_analytics",
    "get_roles_analytics",
    "get_matches_analytics",
    "get_interviews_analytics",
    "get_processing_analytics",
    "get_system_analytics",
]
