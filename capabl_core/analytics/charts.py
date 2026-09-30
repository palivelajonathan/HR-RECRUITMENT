"""
Plotly Chart Builders for CAPABL Recruitment Analytics.

Phase 12: Recruitment Analytics.
Implements:
1. Animated line charts (System & Tool activity over time with initial render transition).
2. Bar charts (Tool invocation frequency and knowledge domain inventory).
3. Distribution views (Execution latency histogram and execution status donut).
4. Timeline views (Chronological operational audit stream).

Invariants:
- All charts use subtle single-render animations (never constantly loop or move).
- Dark theme integration strictly adhering to CAPABL color tokens.
- Returns None if insufficient data points are available, allowing UI to render
  the mandatory 'Not enough data yet.' state.
"""

from typing import Dict, Any, List, Optional
import plotly.graph_objects as go


THEME_COLORS = {
    "canvas_bg": "rgba(0,0,0,0)",
    "card_bg": "rgba(18, 24, 38, 0.72)",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "border_muted": "rgba(255, 255, 255, 0.08)",
    "grid_color": "rgba(255, 255, 255, 0.05)",
    "indigo": "#6366F1",
    "cyan": "#06B6D4",
    "emerald": "#10B981",
    "amber": "#F59E0B",
    "rose": "#F43F5E",
    "purple": "#A855F7",
}

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#F8FAFC", size=12),
    margin=dict(l=24, r=24, t=36, b=24),
    transition={"duration": 450, "easing": "cubic-in-out"},
)


def build_activity_line_chart(hourly_timeline: List[Dict[str, Any]]) -> Optional[go.Figure]:
    """
    Constructs an animated line chart of temporal activity over time.
    Shows Total Events, Tool Operations, and Agent Trajectories.
    Returns None if fewer than 2 data points exist.
    """
    if not hourly_timeline or len(hourly_timeline) < 2:
        return None

    x_vals = [item["display_time"] for item in hourly_timeline]
    y_total = [item["total_events"] for item in hourly_timeline]
    y_tools = [item["tool_events"] for item in hourly_timeline]
    y_agents = [item["agent_events"] for item in hourly_timeline]

    fig = go.Figure()

    # Total System Events Trace (Indigo Spline with Gradient Fill)
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_total,
            name="Total Events",
            mode="lines+markers",
            line=dict(color=THEME_COLORS["indigo"], width=2.5, shape="spline"),
            marker=dict(size=5, color=THEME_COLORS["indigo"], symbol="circle"),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.09)",
            hovertemplate="<b>Total Events</b>: %{y}<br>Time: %{x}<extra></extra>",
        )
    )

    # Tool Invocations Trace (Cyan Spline)
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_tools,
            name="Tool Invocations",
            mode="lines+markers",
            line=dict(color=THEME_COLORS["cyan"], width=2, shape="spline"),
            marker=dict(size=4, color=THEME_COLORS["cyan"]),
            hovertemplate="<b>Tool Calls</b>: %{y}<br>Time: %{x}<extra></extra>",
        )
    )

    # Agent Trajectories Trace (Emerald Spline)
    if any(a > 0 for a in y_agents):
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_agents,
                name="Agent Trajectories",
                mode="lines+markers",
                line=dict(color=THEME_COLORS["emerald"], width=1.8, dash="dot", shape="spline"),
                marker=dict(size=4, color=THEME_COLORS["emerald"]),
                hovertemplate="<b>Agent Runs</b>: %{y}<br>Time: %{x}<extra></extra>",
            )
        )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>Temporal Activity Volume</b> <span style='font-size:11px;color:#94A3B8;'>(Events & Tool Invocations by Hour)</span>",
            font=dict(size=14, color="#F8FAFC"),
        ),
        xaxis=dict(
            gridcolor=THEME_COLORS["grid_color"],
            linecolor=THEME_COLORS["border_muted"],
            tickfont=dict(size=10, color=THEME_COLORS["text_secondary"]),
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor=THEME_COLORS["grid_color"],
            linecolor=THEME_COLORS["border_muted"],
            tickfont=dict(size=10, color=THEME_COLORS["text_secondary"]),
            showgrid=True,
            zeroline=False,
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=THEME_COLORS["text_secondary"]),
        ),
    )

    return fig


def build_tools_bar_chart(tool_counts: Dict[str, int], top_n: int = 8) -> Optional[go.Figure]:
    """
    Constructs a horizontal bar chart displaying frequency of tool invocations.
    Returns None if no tool invocations have been recorded.
    """
    if not tool_counts or sum(tool_counts.values()) == 0:
        return None

    # Sort descending and take top N
    sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    # Reverse for ascending horizontal display
    sorted_tools = list(reversed(sorted_tools))

    names = [k.replace("mcp::", "⚡ ").replace("_", " ").title() for k, _ in sorted_tools]
    values = [v for _, v in sorted_tools]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker=dict(
                color=THEME_COLORS["indigo"],
                line=dict(color="rgba(99, 102, 241, 0.4)", width=1),
                opacity=0.85,
            ),
            text=values,
            textposition="auto",
            textfont=dict(color="#F8FAFC", size=11, family="Plus Jakarta Sans"),
            hovertemplate="<b>%{y}</b>: %{x} executions<extra></extra>",
        )
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text=f"<b>Top Subsystem & Tool Invocations</b> <span style='font-size:11px;color:#94A3B8;'>(Top {len(sorted_tools)})</span>",
            font=dict(size=14, color="#F8FAFC"),
        ),
        xaxis=dict(
            gridcolor=THEME_COLORS["grid_color"],
            linecolor=THEME_COLORS["border_muted"],
            tickfont=dict(size=10, color=THEME_COLORS["text_secondary"]),
            showgrid=True,
        ),
        yaxis=dict(
            linecolor=THEME_COLORS["border_muted"],
            tickfont=dict(size=11, color=THEME_COLORS["text_primary"]),
            autorange=True,
        ),
        showlegend=False,
    )

    return fig


def build_domain_inventory_bar_chart(chunks_by_domain: Dict[str, int]) -> Optional[go.Figure]:
    """
    Constructs a vertical bar chart displaying vector chunks per isolated domain.
    Returns None if all domain chunk counts are 0.
    """
    total = sum(chunks_by_domain.values())
    if total == 0:
        return None

    labels = ["Candidate Resumes", "Job Requisitions", "Compliance Policies", "System Index"]
    keys = ["resume", "job_description", "policy", "other"]
    counts = [chunks_by_domain.get(k, 0) for k in keys]
    colors = [THEME_COLORS["indigo"], THEME_COLORS["cyan"], THEME_COLORS["emerald"], THEME_COLORS["text_muted"]]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=counts,
            marker=dict(
                color=colors,
                line=dict(color="rgba(255, 255, 255, 0.12)", width=1),
                opacity=0.9,
            ),
            text=counts,
            textposition="auto",
            textfont=dict(color="#F8FAFC", size=11, family="Plus Jakarta Sans"),
            hovertemplate="<b>%{x}</b>: %{y} chunks<extra></extra>",
        )
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>Knowledge Inventory by Isolated Domain</b> <span style='font-size:11px;color:#94A3B8;'>(Indexed Chunks)</span>",
            font=dict(size=14, color="#F8FAFC"),
        ),
        xaxis=dict(
            linecolor=THEME_COLORS["border_muted"],
            tickfont=dict(size=11, color=THEME_COLORS["text_secondary"]),
        ),
        yaxis=dict(
            gridcolor=THEME_COLORS["grid_color"],
            linecolor=THEME_COLORS["border_muted"],
            tickfont=dict(size=10, color=THEME_COLORS["text_secondary"]),
            showgrid=True,
        ),
        showlegend=False,
    )

    return fig


def build_latency_distribution_chart(durations: List[float]) -> Optional[go.Figure]:
    """
    Constructs a distribution histogram of operational execution latency (ms).
    Computes and marks P50 and P90 thresholds with vertical reference lines.
    Returns None if fewer than 2 duration samples exist.
    """
    if not durations or len(durations) < 2:
        return None

    s_dur = sorted(durations)
    n = len(s_dur)
    p50 = s_dur[int(n * 0.50)]
    p90 = s_dur[int(n * 0.90)]

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=durations,
            name="Latency",
            marker=dict(
                color=THEME_COLORS["indigo"],
                line=dict(color="rgba(99, 102, 241, 0.4)", width=1),
                opacity=0.75,
            ),
            hovertemplate="Latency: %{x:.1f} ms<br>Count: %{y}<extra></extra>",
        )
    )

    # Add Median (P50) Line
    fig.add_vline(
        x=p50,
        line_width=2,
        line_dash="dash",
        line_color=THEME_COLORS["cyan"],
        annotation_text=f"P50: {p50:.1f}ms",
        annotation_position="top left",
        annotation_font=dict(size=10, color=THEME_COLORS["cyan"]),
    )

    # Add P90 Line
    fig.add_vline(
        x=p90,
        line_width=2,
        line_dash="dot",
        line_color=THEME_COLORS["amber"],
        annotation_text=f"P90: {p90:.1f}ms",
        annotation_position="top right",
        annotation_font=dict(size=10, color=THEME_COLORS["amber"]),
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>Execution Duration Distribution</b> <span style='font-size:11px;color:#94A3B8;'>(Tool & Subsystem Latency in ms)</span>",
            font=dict(size=14, color="#F8FAFC"),
        ),
        xaxis=dict(
            title=dict(text="Latency (ms)", font=dict(size=11, color=THEME_COLORS["text_secondary"])),
            gridcolor=THEME_COLORS["grid_color"],
            linecolor=THEME_COLORS["border_muted"],
            tickfont=dict(size=10, color=THEME_COLORS["text_secondary"]),
            showgrid=True,
        ),
        yaxis=dict(
            title=dict(text="Operation Count", font=dict(size=11, color=THEME_COLORS["text_secondary"])),
            gridcolor=THEME_COLORS["grid_color"],
            linecolor=THEME_COLORS["border_muted"],
            tickfont=dict(size=10, color=THEME_COLORS["text_secondary"]),
            showgrid=True,
        ),
        showlegend=False,
    )

    return fig


def build_status_donut_chart(status_distribution: Dict[str, int]) -> Optional[go.Figure]:
    """
    Constructs a donut chart showing the breakdown of execution statuses
    (Success, Blocked, Flagged, Error).
    Returns None if status_distribution is empty.
    """
    if not status_distribution or sum(status_distribution.values()) == 0:
        return None

    status_color_map = {
        "success": THEME_COLORS["emerald"],
        "confirmed": THEME_COLORS["emerald"],
        "blocked": THEME_COLORS["amber"],
        "flagged": THEME_COLORS["purple"],
        "error": THEME_COLORS["rose"],
    }

    labels = []
    values = []
    colors = []

    for status_name, cnt in sorted(status_distribution.items(), key=lambda x: x[1], reverse=True):
        if cnt > 0:
            labels.append(status_name.capitalize())
            values.append(cnt)
            colors.append(status_color_map.get(status_name.lower(), THEME_COLORS["indigo"]))

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker=dict(colors=colors, line=dict(color="#080B11", width=2)),
            textinfo="percent+label",
            textposition="inside",
            insidetextorientation="horizontal",
            textfont=dict(size=11, color="#F8FAFC", family="Plus Jakarta Sans"),
            hovertemplate="<b>%{label}</b>: %{value} events (%{percent})<extra></extra>",
        )
    )

    total_events = sum(values)

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>Execution Outcome Distribution</b>",
            font=dict(size=14, color="#F8FAFC"),
        ),
        annotations=[
            dict(
                text=f"<b>{total_events:,}</b><br><span style='font-size:10px;color:#94A3B8;'>Events</span>",
                x=0.5,
                y=0.5,
                font=dict(size=14, color="#F8FAFC", family="Plus Jakarta Sans"),
                showarrow=False,
            )
        ],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=THEME_COLORS["text_secondary"]),
        ),
    )

    return fig
