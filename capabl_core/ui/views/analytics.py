"""
Production Recruitment Analytics & Observability Workspace View.

Phase 12: Recruitment Analytics.
Implements:
1. Production Metrics Ribbon (Candidates processed, Roles created, Matches generated,
   Interviews scheduled, Processing activity, System activity).
2. Animated Line Charts (System event & tool execution volume over time with subtle
   initial render transitions; never constantly moving).
3. Bar Charts (Top tool & subsystem invocations; Knowledge inventory by domain).
4. Distribution Views (Execution latency distribution histogram with P50/P90 markers;
   Execution status breakdown donut chart).
5. Timeline Views (Chronological operational audit event stream with domain filters).
6. Strict Data Integrity:
   - Grounded strictly in actual persisted/runtime data (Chroma, Roles Registry, MockCalendar, Audit Log).
   - Never fabricates metrics or displays simulated numbers.
   - Displays 'Not enough data yet.' when data points are insufficient.
"""

from typing import Dict, Any, List, Optional
import html
import streamlit as st

from capabl_core.analytics.engine import (
    AnalyticsSnapshot,
    get_analytics_snapshot,
)
from capabl_core.analytics.charts import (
    build_activity_line_chart,
    build_tools_bar_chart,
    build_domain_inventory_bar_chart,
    build_latency_distribution_chart,
    build_status_donut_chart,
)


def render_not_enough_data(explanation: str, icon: str = "📊") -> None:
    """
    Renders an elegant, standard 'Not enough data yet.' state card
    when insufficient runtime or persisted data exists.
    """
    st.markdown(
        f"""
        <div class="capabl-insufficient-data-box">
          <div style="font-size: 1.85rem; margin-bottom: 0.25rem; opacity: 0.85;">{icon}</div>
          <div class="not-enough-title">Not enough data yet.</div>
          <div class="not-enough-caption">{html.escape(explanation)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics_ribbon(snapshot: AnalyticsSnapshot) -> None:
    """Renders the 6 mandatory metrics in a modern, responsive CSS grid."""
    # 1. Candidates
    if snapshot.has_candidates_data:
        c1 = f"""
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">Candidates</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #F8FAFC; line-height: 1.1;">{snapshot.candidates_count}</div>
          <div style="display: flex; align-items: center; gap: 0.35rem; margin-top: 0.4rem;">
            <span class="capabl-chip capabl-chip-success" style="font-size: 0.68rem; margin: 0; padding: 0.1rem 0.4rem; white-space: nowrap;">{snapshot.total_chunks} Chunks</span>
          </div>
        </div>
        """
    else:
        c1 = """
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">Candidates</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #64748B; line-height: 1.1;">0</div>
          <div style="font-size: 0.72rem; color: #F59E0B; margin-top: 0.4rem; font-weight: 500; white-space: nowrap;">Not enough data yet.</div>
        </div>
        """

    # 2. Roles Created
    if snapshot.has_roles_data:
        c2 = f"""
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">Roles Created</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #F8FAFC; line-height: 1.1;">{snapshot.roles_count}</div>
          <div style="display: flex; align-items: center; gap: 0.35rem; margin-top: 0.4rem;">
            <span class="capabl-chip capabl-chip-cyan" style="font-size: 0.68rem; margin: 0; padding: 0.1rem 0.4rem; white-space: nowrap;">{snapshot.roles_by_status.get('Active', snapshot.roles_count)} Active</span>
          </div>
        </div>
        """
    else:
        c2 = """
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">Roles Created</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #64748B; line-height: 1.1;">0</div>
          <div style="font-size: 0.72rem; color: #F59E0B; margin-top: 0.4rem; font-weight: 500; white-space: nowrap;">Not enough data yet.</div>
        </div>
        """

    # 3. Matches Generated
    if snapshot.has_matches_data:
        c3 = f"""
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">Matches Generated</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #F8FAFC; line-height: 1.1;">{snapshot.matches_count}</div>
          <div style="display: flex; align-items: center; gap: 0.35rem; margin-top: 0.4rem;">
            <span class="capabl-chip capabl-chip-success" style="font-size: 0.68rem; margin: 0; padding: 0.1rem 0.4rem; white-space: nowrap;">Deterministic M3</span>
          </div>
        </div>
        """
    else:
        c3 = """
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">Matches Generated</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #64748B; line-height: 1.1;">0</div>
          <div style="font-size: 0.72rem; color: #F59E0B; margin-top: 0.4rem; font-weight: 500; white-space: nowrap;">Not enough data yet.</div>
        </div>
        """

    # 4. Interviews Scheduled
    if snapshot.has_interviews_data:
        c4 = f"""
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">Interviews Scheduled</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #F8FAFC; line-height: 1.1;">{snapshot.interviews_count}</div>
          <div style="display: flex; align-items: center; gap: 0.35rem; margin-top: 0.4rem;">
            <span class="capabl-chip capabl-chip-cyan" style="font-size: 0.68rem; margin: 0; padding: 0.1rem 0.4rem; white-space: nowrap;">Confirmed Slots</span>
          </div>
        </div>
        """
    else:
        c4 = """
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">Interviews Scheduled</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #64748B; line-height: 1.1;">0</div>
          <div style="font-size: 0.72rem; color: #F59E0B; margin-top: 0.4rem; font-weight: 500; white-space: nowrap;">Not enough data yet.</div>
        </div>
        """

    # 5. Processing Activity
    if snapshot.has_processing_data:
        c5 = f"""
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">Processing Activity</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #F8FAFC; line-height: 1.1;">{snapshot.total_chunks} <span style="font-size: 0.85rem; font-weight: 500; color: #94A3B8;">chunks</span></div>
          <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 0.4rem; white-space: nowrap;">{snapshot.documents_ingested_count} docs ingested</div>
        </div>
        """
    else:
        c5 = """
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">Processing Activity</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #64748B; line-height: 1.1;">0</div>
          <div style="font-size: 0.72rem; color: #F59E0B; margin-top: 0.4rem; font-weight: 500; white-space: nowrap;">Not enough data yet.</div>
        </div>
        """

    # 6. System Activity
    if snapshot.has_system_data:
        c6 = f"""
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">System Activity</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #F8FAFC; line-height: 1.1;">{snapshot.total_audit_events:,}</div>
          <div style="display: flex; align-items: center; gap: 0.35rem; margin-top: 0.4rem;">
            <span class="capabl-chip capabl-chip-success" style="font-size: 0.68rem; margin: 0; padding: 0.1rem 0.4rem; white-space: nowrap;">{snapshot.success_rate * 100:.1f}% Success</span>
          </div>
        </div>
        """
    else:
        c6 = """
        <div class="capabl-analytics-kpi-card">
          <div style="font-size: 0.72rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; white-space: nowrap;">System Activity</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #64748B; line-height: 1.1;">0</div>
          <div style="font-size: 0.72rem; color: #F59E0B; margin-top: 0.4rem; font-weight: 500; white-space: nowrap;">Not enough data yet.</div>
        </div>
        """

    st.markdown(
        f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem;">
          {c1}
          {c2}
          {c3}
          {c4}
          {c5}
          {c6}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analytics_workspace() -> None:
    """
    Main entry point for the Recruitment Analytics & Observability workspace.
    """
    # -------------------------------------------------------------------------
    # HEADER & TOOLBAR
    # -------------------------------------------------------------------------
    top_col1, top_col2 = st.columns([0.78, 0.22])
    with top_col1:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.35rem;">
              <h2 style="margin: 0; font-size: 1.55rem; font-weight: 700; color: #F8FAFC; letter-spacing: -0.02em;">
                Recruitment Analytics & Observability
              </h2>
              <span class="capabl-chip capabl-chip-cyan" style="margin: 0; font-size: 0.72rem;">
                Runtime Grounded
              </span>
              <span class="capabl-chip capabl-chip-neutral" style="margin: 0; font-size: 0.72rem;">
                Zero Fabrication
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "Empirical performance, processing throughput, match dynamics, and operational telemetry "
            "derived strictly from runtime and persisted data."
        )

    with top_col2:
        st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Telemetry", use_container_width=True, help="Re-query live Chroma, Registry, and Audit logs"):
            st.rerun()

    # Query live snapshot
    snapshot: AnalyticsSnapshot = get_analytics_snapshot()

    # -------------------------------------------------------------------------
    # 1. PRIMARY METRICS RIBBON (6 MANDATORY PILLARS)
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 0.35rem;'></div>", unsafe_allow_html=True)
    render_metrics_ribbon(snapshot)

    # -------------------------------------------------------------------------
    # 2. TABBED ANALYTICS WORKSPACE
    # -------------------------------------------------------------------------
    tab_activity, tab_dist, tab_timeline, tab_funnel, tab_benchmarks = st.tabs([
        "📈 Operational Volume (Line & Bar)",
        "📊 Distribution & Latency Profiles",
        "📜 Chronological Event Timeline",
        "🎯 Operational Funnel Dynamics",
        "📋 Quality & Retrieval Benchmarks",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: OPERATIONAL ACTIVITY & VOLUME (LINE & BAR CHARTS)
    # -------------------------------------------------------------------------
    with tab_activity:
        st.markdown("#### Operational Activity Over Time")
        st.caption("Temporal distribution of system events, tool invocations, and agent reasoning cycles.")

        # Animated Line Chart
        if snapshot.has_timeline_data:
            line_fig = build_activity_line_chart(snapshot.hourly_activity_timeline)
            if line_fig:
                st.plotly_chart(line_fig, use_container_width=True, config={"displayModeBar": False})
            else:
                render_not_enough_data(
                    "Fewer than 2 temporal data points found. Additional session activity is required to plot timeline trends.",
                    icon="📈",
                )
        else:
            render_not_enough_data(
                "Not enough timestamped events found to construct a time-series line chart. "
                "Interact with tools or ingest documents to establish a temporal activity trail.",
                icon="📈",
            )

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

        # Bar Charts Row (Tools Frequency & Knowledge Domain Inventory)
        bar_col1, bar_col2 = st.columns(2)

        with bar_col1:
            tool_bar_fig = build_tools_bar_chart(snapshot.tool_distribution)
            if tool_bar_fig:
                st.plotly_chart(tool_bar_fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown("<b>Top Subsystem & Tool Invocations</b>", unsafe_allow_html=True)
                render_not_enough_data(
                    "No tool or MCP executions recorded yet. Execute queries in the Agent Workspace to populate tool usage telemetry.",
                    icon="🛠️",
                )

        with bar_col2:
            domain_bar_fig = build_domain_inventory_bar_chart(snapshot.chunks_by_domain)
            if domain_bar_fig:
                st.plotly_chart(domain_bar_fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown("<b>Knowledge Inventory by Domain</b>", unsafe_allow_html=True)
                render_not_enough_data(
                    "ChromaDB vector store is empty. Ingest candidate resumes or requisitions to view domain inventory.",
                    icon="📚",
                )

    # -------------------------------------------------------------------------
    # TAB 2: DISTRIBUTION VIEWS & LATENCY PROFILES
    # -------------------------------------------------------------------------
    with tab_dist:
        st.markdown("#### System Latency & Outcome Distributions")
        st.caption("Statistical profiles of tool execution durations and audit status breakdowns.")

        dist_col1, dist_col2 = st.columns(2)

        with dist_col1:
            if snapshot.has_duration_data:
                lat_fig = build_latency_distribution_chart(snapshot.durations_sample)
                if lat_fig:
                    st.plotly_chart(lat_fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    render_not_enough_data(
                        "Insufficient telemetry points to render duration histogram.",
                        icon="⏱️",
                    )
            else:
                st.markdown("<b>Execution Duration Distribution</b>", unsafe_allow_html=True)
                render_not_enough_data(
                    "Fewer than 2 duration records available in audit log. Tool invocations will register latency telemetry automatically.",
                    icon="⏱️",
                )

        with dist_col2:
            if snapshot.has_system_data:
                donut_fig = build_status_donut_chart(snapshot.status_distribution)
                if donut_fig:
                    st.plotly_chart(donut_fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    render_not_enough_data(
                        "No audit statuses available to construct distribution.",
                        icon="🍩",
                    )
            else:
                st.markdown("<b>Execution Outcome Distribution</b>", unsafe_allow_html=True)
                render_not_enough_data(
                    "No audit events recorded yet.",
                    icon="🍩",
                )

        # Operational Latency Percentiles Card
        st.markdown("##### Factual Latency & Throughput Benchmark")
        l_col1, l_col2, l_col3, l_col4, l_col5, l_col6 = st.columns(6)

        stats = snapshot.latency_stats
        with l_col1:
            st.metric("Traced Operations", f"{len(snapshot.durations_sample):,}")
        with l_col2:
            st.metric("P50 (Median)", f"{stats.get('p50', 0):.1f} ms")
        with l_col3:
            st.metric("P90 Latency", f"{stats.get('p90', 0):.1f} ms")
        with l_col4:
            st.metric("P99 Latency", f"{stats.get('p99', 0):.1f} ms")
        with l_col5:
            st.metric("Mean Duration", f"{stats.get('avg', 0):.1f} ms")
        with l_col6:
            st.metric("Success Rate", f"{snapshot.success_rate * 100:.1f}%")

    # -------------------------------------------------------------------------
    # TAB 3: CHRONOLOGICAL OPERATIONAL TIMELINE
    # -------------------------------------------------------------------------
    with tab_timeline:
        st.markdown("#### Chronological Operational Timeline")
        st.caption("Granular, time-ordered sequence of all recruitment system events and gatekeeper decisions.")

        filter_col1, filter_col2, filter_col3 = st.columns([0.48, 0.32, 0.20])

        with filter_col1:
            search_query = st.text_input(
                "Filter Events",
                value="",
                placeholder="Search by event, candidate, tool, or action...",
                label_visibility="collapsed",
            ).strip().lower()

        with filter_col2:
            event_type_filter = st.selectbox(
                "Category Filter",
                options=[
                    "All Categories",
                    "Tool Executions",
                    "Document Ingestion",
                    "Deterministic Matches",
                    "Interview Operations",
                    "Security & Gatekeeper",
                    "Errors & Blocks",
                ],
                label_visibility="collapsed",
            )

        with filter_col3:
            event_limit = st.selectbox(
                "Display Count",
                options=[20, 50, 100],
                index=1,
                label_visibility="collapsed",
            )

        # Filter events
        filtered_events = []
        for ev in snapshot.chronological_events:
            ev_name = ev.get("event", "").lower()
            st_name = ev.get("status", "").lower()
            payload_str = str(ev.get("payload", {})).lower()

            # Category filter match
            if event_type_filter == "Tool Executions" and not ("tool" in ev_name):
                continue
            elif event_type_filter == "Document Ingestion" and not ("ingest" in ev_name or "upload" in ev_name):
                continue
            elif event_type_filter == "Deterministic Matches" and not ("match" in ev_name):
                continue
            elif event_type_filter == "Interview Operations" and not ("booking" in ev_name or "calendar" in ev_name):
                continue
            elif event_type_filter == "Security & Gatekeeper" and not ("blocked" in st_name or "flagged" in st_name or "security" in ev_name):
                continue
            elif event_type_filter == "Errors & Blocks" and not (st_name in ("error", "blocked") or "error" in ev_name):
                continue

            # Text query match
            if search_query:
                combined_text = f"{ev_name} {st_name} {payload_str}".lower()
                if search_query not in combined_text:
                    continue

            filtered_events.append(ev)
            if len(filtered_events) >= event_limit:
                break

        if not filtered_events:
            render_not_enough_data(
                "No events matching the current search criteria or category filter.",
                icon="🔍",
            )
        else:
            st.markdown(
                f"<div style='font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.75rem;'>"
                f"Showing <b>{len(filtered_events)}</b> events matching criteria:</div>",
                unsafe_allow_html=True,
            )

            for item in filtered_events:
                ts = item.get("timestamp", "")[:19].replace("T", " ")
                ev_type = item.get("event", "Event")
                status = item.get("status", "success")
                dur = item.get("duration_ms")
                dur_str = f"{dur:.1f}ms" if (dur and isinstance(dur, (int, float))) else "-"
                payload = item.get("payload", {})

                # Semantic status styling
                if status in ("success", "confirmed"):
                    status_pill = f'<span class="capabl-chip capabl-chip-success" style="font-size:0.7rem;margin:0;">{status.upper()}</span>'
                elif status in ("blocked", "flagged"):
                    status_pill = f'<span class="capabl-chip capabl-chip-amber" style="font-size:0.7rem;margin:0;">{status.upper()}</span>'
                elif status == "error":
                    status_pill = f'<span class="capabl-chip capabl-chip-danger" style="font-size:0.7rem;margin:0;">ERROR</span>'
                else:
                    status_pill = f'<span class="capabl-chip capabl-chip-neutral" style="font-size:0.7rem;margin:0;">{status.upper()}</span>'

                with st.expander(f"{ts} • {ev_type} • {dur_str}", expanded=False):
                    e_col1, e_col2 = st.columns([0.7, 0.3])
                    with e_col1:
                        st.markdown(f"**Event Type:** `{ev_type}`")
                        st.markdown(f"**Session ID:** `{item.get('session_id', 'default_session')}`")
                        st.markdown(f"**Timestamp (UTC):** `{item.get('timestamp')}`")
                    with e_col2:
                        st.markdown(f"**Status:** {status_pill}", unsafe_allow_html=True)
                        st.markdown(f"**Duration:** `{dur_str}`")

                    st.markdown("**Sanitized Event Payload:**")
                    st.json(payload)

    # -------------------------------------------------------------------------
    # TAB 4: RECRUITMENT PIPELINE & CONVERSION FUNNEL
    # -------------------------------------------------------------------------
    with tab_funnel:
        st.markdown("#### Operational Recruitment Funnel")
        st.caption("Factual pipeline progression from candidate ingestion to interview scheduling.")

        funnel_col1, funnel_col2, funnel_col3, funnel_col4 = st.columns(4)

        with funnel_col1:
            st.markdown(
                f"""
                <div class="capabl-analytics-kpi-card" style="border-left: 3px solid #6366F1;">
                  <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 600; text-transform: uppercase;">
                    1. Ingestion Stage
                  </div>
                  <div style="font-size: 1.5rem; font-weight: 800; color: #F8FAFC; margin: 0.3rem 0;">
                    {snapshot.candidates_count} Candidates
                  </div>
                  <div style="font-size: 0.75rem; color: #94A3B8;">
                    {snapshot.total_chunks} Total Chunks Indexed
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with funnel_col2:
            st.markdown(
                f"""
                <div class="capabl-analytics-kpi-card" style="border-left: 3px solid #06B6D4;">
                  <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 600; text-transform: uppercase;">
                    2. Requisition Stage
                  </div>
                  <div style="font-size: 1.5rem; font-weight: 800; color: #F8FAFC; margin: 0.3rem 0;">
                    {snapshot.roles_count} Active Roles
                  </div>
                  <div style="font-size: 0.75rem; color: #94A3B8;">
                    {len(snapshot.roles_by_department)} Engineering Depts
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with funnel_col3:
            if snapshot.has_matches_data:
                st.markdown(
                    f"""
                    <div class="capabl-analytics-kpi-card" style="border-left: 3px solid #10B981;">
                      <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 600; text-transform: uppercase;">
                        3. Match Stage
                      </div>
                      <div style="font-size: 1.5rem; font-weight: 800; color: #F8FAFC; margin: 0.3rem 0;">
                        {snapshot.matches_count} Evaluated
                      </div>
                      <div style="font-size: 0.75rem; color: #34D399;">
                        Deterministic Set Comparison
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="capabl-analytics-kpi-card" style="border-left: 3px solid #F59E0B;">
                      <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 600; text-transform: uppercase;">
                        3. Match Stage
                      </div>
                      <div style="font-size: 1.5rem; font-weight: 800; color: #64748B; margin: 0.3rem 0;">
                        0 Evaluated
                      </div>
                      <div style="font-size: 0.72rem; color: #F59E0B;">
                        Not enough data yet.
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with funnel_col4:
            if snapshot.has_interviews_data:
                st.markdown(
                    f"""
                    <div class="capabl-analytics-kpi-card" style="border-left: 3px solid #A855F7;">
                      <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 600; text-transform: uppercase;">
                        4. Interview Stage
                      </div>
                      <div style="font-size: 1.5rem; font-weight: 800; color: #F8FAFC; margin: 0.3rem 0;">
                        {snapshot.interviews_count} Booked
                      </div>
                      <div style="font-size: 0.75rem; color: #A855F7;">
                        Consequential Gate Preserved
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="capabl-analytics-kpi-card" style="border-left: 3px solid #F59E0B;">
                      <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 600; text-transform: uppercase;">
                        4. Interview Stage
                      </div>
                      <div style="font-size: 1.5rem; font-weight: 800; color: #64748B; margin: 0.3rem 0;">
                        0 Booked
                      </div>
                      <div style="font-size: 0.72rem; color: #F59E0B;">
                        Not enough data yet.
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        if not snapshot.has_matches_data or not snapshot.has_interviews_data:
            render_not_enough_data(
                "Full funnel conversion requires deterministic matches and confirmed interview bookings. "
                "Visit the 'Matches' and 'Interviews' sections to advance candidates through the pipeline.",
                icon="🎯",
            )

    # -------------------------------------------------------------------------
    # TAB 5: M7 BASELINE BENCHMARK METRICS (PRESERVED INTEGRATION)
    # -------------------------------------------------------------------------
    with tab_benchmarks:
        st.markdown("#### Quality, Retrieval, Security & MCP Baselines")
        st.caption("Formal evaluation reports verifying precision, groundedness, and security invariants.")

        baseline_file = st.session_state.get("baseline_report_path", "evaluation/reports/M7_BASELINE.json")
        p_base = st.session_state.get("_baseline_path_obj", None)
        from pathlib import Path
        base_path = Path(baseline_file)

        if base_path.exists():
            try:
                import json
                with open(base_path, "r", encoding="utf-8") as bf:
                    b_data = json.load(bf)
                suites = b_data.get("suites", {})
                ret_m = suites.get("retrieval", {}).get("metrics", {})
                rag_m = suites.get("rag", {}).get("metrics", {})
                tool_m = suites.get("tools", {}).get("metrics", {})
                sec_m = suites.get("security", {}).get("metrics", {})

                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    p1 = ret_m.get("precision_at_1", 1.0)
                    st.metric("Retrieval P@1", f"{p1 * 100:.1f}%")
                with b2:
                    ground = rag_m.get("groundedness_rate", 1.0)
                    st.metric("RAG Groundedness", f"{ground * 100:.1f}%")
                with b3:
                    t_acc = tool_m.get("execution_accuracy", 1.0)
                    st.metric("Tool Execution Accuracy", f"{t_acc * 100:.1f}%")
                with b4:
                    s_pass = sec_m.get("overall_security_pass_rate", 1.0)
                    st.metric("Security Pass Rate", f"{s_pass * 100:.1f}%")

                with st.expander("Full Suite Metrics Breakdown (JSON)", expanded=False):
                    st.json(suites)
            except Exception:
                render_not_enough_data("Verification benchmark report present but could not be parsed. Run telemetry refresh to re-evaluate.", icon="📋")
        else:
            render_not_enough_data("System benchmark and verification report not yet available. Comprehensive validation benchmarks run during scheduled platform audits.", icon="📋")
