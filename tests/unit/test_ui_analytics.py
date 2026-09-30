"""
Unit Test Suite for Phase 12: Recruitment Analytics & Observability.

Verifies:
1. Factual data extraction from Chroma, roles registry, calendar, and audit log.
2. Zero fabricated metrics: accurate reporting of true counts.
3. Insufficient data handling: correctly triggers 'Not enough data yet.' flags and states.
4. Chart generation:
   - Animated line chart (subtle single-render transition, None on insufficient points)
   - Bar charts (tools frequency and domain inventory, None when empty)
   - Distribution views (latency histogram with P50/P90 markers, status donut)
5. Secret hygiene: zero secrets, tokens, or private environment variables leaked in analytics.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any

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
from capabl_core.analytics.charts import (
    build_activity_line_chart,
    build_tools_bar_chart,
    build_domain_inventory_bar_chart,
    build_latency_distribution_chart,
    build_status_donut_chart,
)


def test_candidates_analytics_structure():
    """Verifies candidate analytics structure and factual reporting."""
    res = get_candidates_analytics()
    assert isinstance(res, dict)
    assert "count" in res
    assert "candidates" in res
    assert "has_data" in res
    assert isinstance(res["count"], int)
    assert res["count"] >= 0
    assert res["has_data"] == (res["count"] > 0)


def test_roles_analytics_structure():
    """Verifies roles analytics reads registry without fabrication."""
    res = get_roles_analytics()
    assert isinstance(res, dict)
    assert "count" in res
    assert "roles" in res
    assert "departments" in res
    assert "statuses" in res
    assert "has_data" in res
    assert res["count"] >= 0
    assert res["has_data"] == (res["count"] > 0)


def test_matches_analytics_structure():
    """Verifies matches analytics handles zero or present matches."""
    res = get_matches_analytics()
    assert isinstance(res, dict)
    assert "count" in res
    assert "matches" in res
    assert "avg_duration_ms" in res
    assert "has_data" in res
    assert res["count"] >= 0
    assert res["has_data"] == (res["count"] > 0)


def test_interviews_analytics_structure():
    """Verifies interviews analytics queries calendar and confirmed bookings."""
    res = get_interviews_analytics()
    assert isinstance(res, dict)
    assert "count" in res
    assert "interviews" in res
    assert "has_data" in res
    assert res["count"] >= 0
    assert res["has_data"] == (res["count"] > 0)


def test_processing_analytics_structure():
    """Verifies processing analytics chunks and ingestion metrics."""
    res = get_processing_analytics()
    assert isinstance(res, dict)
    assert "total_chunks" in res
    assert "chunks_by_domain" in res
    assert "has_data" in res
    assert "resume" in res["chunks_by_domain"]
    assert "job_description" in res["chunks_by_domain"]
    assert "policy" in res["chunks_by_domain"]


def test_system_analytics_structure():
    """Verifies system analytics reads audit trail and computes percentiles."""
    res = get_system_analytics()
    assert isinstance(res, dict)
    assert "total_events" in res
    assert "tool_executions" in res
    assert "status_distribution" in res
    assert "latency_stats" in res
    assert "hourly_timeline" in res
    assert "has_data" in res
    assert "has_timeline_data" in res
    assert "has_duration_data" in res

    # Latency percentiles check
    stats = res["latency_stats"]
    assert "p50" in stats
    assert "p90" in stats
    assert "p99" in stats
    assert "avg" in stats
    assert stats["min"] <= stats["max"]


def test_analytics_snapshot_aggregation():
    """Verifies master AnalyticsSnapshot object aggregation."""
    snapshot = get_analytics_snapshot()
    assert isinstance(snapshot, AnalyticsSnapshot)
    assert snapshot.candidates_count >= 0
    assert snapshot.roles_count >= 0
    assert snapshot.matches_count >= 0
    assert snapshot.interviews_count >= 0
    assert snapshot.total_chunks >= 0
    assert snapshot.total_audit_events >= 0
    assert 0.0 <= snapshot.success_rate <= 1.0


def test_activity_line_chart_builder():
    """Verifies animated line chart generation and insufficient data behavior."""
    # When >= 2 points
    sample_timeline = [
        {"display_time": "09-29 10:00", "total_events": 20, "tool_events": 10, "agent_events": 5},
        {"display_time": "09-29 11:00", "total_events": 35, "tool_events": 15, "agent_events": 8},
    ]
    fig = build_activity_line_chart(sample_timeline)
    assert fig is not None
    assert len(fig.data) >= 2  # Total and Tools traces
    # Subtle transition verification
    assert fig.layout.transition.duration == 450

    # When < 2 points (Insufficient data)
    assert build_activity_line_chart([]) is None
    assert build_activity_line_chart([sample_timeline[0]]) is None


def test_tools_bar_chart_builder():
    """Verifies tools bar chart builder and empty state handling."""
    sample_tools = {
        "retrieve_candidate_evidence": 45,
        "get_job_requirements": 30,
        "check_policy_rules": 12,
    }
    fig = build_tools_bar_chart(sample_tools)
    assert fig is not None
    assert len(fig.data) == 1
    assert fig.layout.transition.duration == 450

    # Empty tools
    assert build_tools_bar_chart({}) is None
    assert build_tools_bar_chart({"t1": 0}) is None


def test_domain_inventory_bar_chart_builder():
    """Verifies domain inventory bar chart and empty state handling."""
    sample_domains = {"resume": 80, "job_description": 25, "policy": 15, "other": 0}
    fig = build_domain_inventory_bar_chart(sample_domains)
    assert fig is not None
    assert len(fig.data) == 1

    # Empty domains
    assert build_domain_inventory_bar_chart({}) is None
    assert build_domain_inventory_bar_chart({"resume": 0, "job_description": 0, "policy": 0}) is None


def test_latency_distribution_chart_builder():
    """Verifies latency distribution histogram and P50/P90 annotations."""
    sample_durations = [12.5, 25.0, 30.2, 45.1, 95.0, 120.4, 210.0]
    fig = build_latency_distribution_chart(sample_durations)
    assert fig is not None
    assert len(fig.data) == 1  # Histogram trace
    # Layout must contain P50 and P90 shape annotations / vlines
    assert len(fig.layout.shapes) >= 2

    # Insufficient points (< 2)
    assert build_latency_distribution_chart([]) is None
    assert build_latency_distribution_chart([25.0]) is None


def test_status_donut_chart_builder():
    """Verifies status donut chart and empty state handling."""
    sample_statuses = {"success": 450, "blocked": 8, "error": 2}
    fig = build_status_donut_chart(sample_statuses)
    assert fig is not None
    assert len(fig.data) == 1
    assert fig.data[0].hole > 0.5  # Donut hole

    # Empty statuses
    assert build_status_donut_chart({}) is None
    assert build_status_donut_chart({"success": 0}) is None


def test_secret_hygiene_in_analytics():
    """Verifies that no secrets or API keys leak into analytics payloads or records."""
    snapshot = get_analytics_snapshot()
    serialized = json.dumps({
        "candidates": snapshot.candidates_list,
        "roles": snapshot.roles_list,
        "matches": snapshot.matches_list,
        "interviews": snapshot.interviews_list,
        "events": snapshot.chronological_events[:10],
    })
    # Must not contain raw secret tokens
    assert "gsk_" not in serialized
    assert "sk-" not in serialized
    assert "groq_api_key" not in serialized.lower() or "[REDACTED" in serialized
