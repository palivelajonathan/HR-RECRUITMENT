"""
Production Top Bar for CAPABL Recruitment Intelligence OS.

Phase 2: Production Application Shell.
Renders workspace identity, global command search trigger, live system status,
notifications preview, and user account menu using Streamlit native columns.
"""

from typing import Optional, Dict, Any
import streamlit as st

from capabl_core.health import check_readiness
from capabl_core.llm import get_active_provider_name


def render_topbar() -> None:
    """Renders the top application bar with workspace identity, search, and status."""
    provider_name = get_active_provider_name()
    health = check_readiness()
    is_ready = health.get("ready", True)

    provider_label = "Groq Cloud" if provider_name != "ollama" else "Ollama Local"
    status_text = "Operational" if is_ready else "Degraded"

    tb_left, tb_right = st.columns([1, 1])
    with tb_left:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; padding: 4px 0;">
              <div style="background: linear-gradient(135deg, #6366F1 0%, #06B6D4 100%); width: 32px; height: 32px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.1rem; color: #FFFFFF; box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);">C</div>
              <span style="font-size: 1.15rem; font-weight: 700; letter-spacing: -0.02em; color: #F8FAFC;">CAPABL</span>
              <span style="font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; background: rgba(99, 102, 241, 0.15); color: #A5B4FC; border: 1px solid rgba(99, 102, 241, 0.3); padding: 2px 8px; border-radius: 9999px;">TALENT OS</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tb_right:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 12px; padding: 4px 0;">
              <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(16, 185, 129, 0.10); border: 1px solid rgba(16, 185, 129, 0.28); border-radius: 9999px; padding: 4px 12px; font-size: 0.75rem; font-weight: 600; color: #34D399;">
                <span class="capabl-status-dot-active"></span>
                <span>{status_text} • {provider_label}</span>
              </div>
              <div style="display: flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 8px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06);">
                <div style="width: 24px; height: 24px; border-radius: 50%; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; color: #FFFFFF;">JD</div>
                <span style="font-size: 0.8rem; font-weight: 600; color: #F8FAFC;">Jonathan D.</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height: 4px;"></div>', unsafe_allow_html=True)

    # Interactive Global Search Trigger Bar directly under topbar
    col_search, col_notif = st.columns([5, 1])
    with col_search:
        search_label = "🔍  Search candidates, job requisitions, policies, or actions... (Ctrl+K / ⌘K)"
        if st.button(search_label, key="btn_trigger_search_palette", use_container_width=True):
            st.session_state["show_command_palette"] = True
            st.rerun()

    with col_notif:
        unread_count = len(st.session_state.get("notifications", [1, 2]))
        if st.button(f"🔔 {unread_count} Alerts", key="btn_notifications_toggle", use_container_width=True):
            st.session_state["show_notifications"] = not st.session_state.get("show_notifications", False)
            st.rerun()

    # Expandable Notifications Drawer
    if st.session_state.get("show_notifications", False):
        with st.container():
            from enhancement.security.audit_logger import DEFAULT_AUDIT_LOGGER
            import html

            recent_events = []
            try:
                recent_events = DEFAULT_AUDIT_LOGGER.query_events(limit=4)
            except Exception:
                pass

            notif_html = [
                """
                <div class="capabl-glass-card" style="margin-bottom: 1rem; border-color: rgba(99, 102, 241, 0.3);">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <strong style="color: #F8FAFC; font-size: 0.9rem;">Workspace Audit Activity</strong>
                    <span style="color: #94A3B8; font-size: 0.75rem;">Real-time</span>
                  </div>
                """
            ]

            if recent_events:
                for ev in recent_events[:3]:
                    ev_type = html.escape(str(ev.get("event", "Operational Event")).replace("_", " ").title())
                    ev_status = html.escape(str(ev.get("status", "info")).upper())
                    ev_time = str(ev.get("timestamp", ""))[-8:]
                    status_color = "#34D399" if ev_status in ("SUCCESS", "CONFIRMED", "READY") else "#F59E0B"
                    notif_html.append(
                        f"""
                        <div style="font-size: 0.8rem; color: #CBD5E1; padding: 0.35rem 0; border-bottom: 1px solid rgba(255,255,255,0.06); display: flex; justify-content: space-between; align-items: center;">
                          <div>
                            <span style="color: {status_color}; font-weight: 700; margin-right: 0.35rem;">●</span>
                            <strong>{ev_type}</strong>
                          </div>
                          <span style="font-family: monospace; font-size: 0.72rem; color: #94A3B8;">{ev_time} UTC</span>
                        </div>
                        """
                    )
            else:
                notif_html.append(
                    """
                    <div style="font-size: 0.8rem; color: #94A3B8; padding: 0.5rem 0; text-align: center;">
                      All systems nominal. No unread security or operational alerts.
                    </div>
                    """
                )

            notif_html.append("</div>")
            st.markdown("".join(notif_html), unsafe_allow_html=True)
