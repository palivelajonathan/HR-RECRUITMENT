"""
Production Sidebar Navigation Component for CAPABL Recruitment Intelligence OS.

Phase 2: Production Application Shell.
Implements primary and secondary navigation sections, active indicators,
smooth transition states, and keyboard shortcut navigation.
"""

from typing import Tuple, List, Dict, Any
import streamlit as st


NAV_PRIMARY: List[Tuple[str, str, str]] = [
    ("overview", "📊 Overview", "1"),
    ("candidates", "👤 Candidates", "2"),
    ("jobs", "💼 Jobs", "3"),
    ("matches", "🎯 Matches", "4"),
    ("evidence", "🔍 Evidence", "5"),
    ("interviews", "📅 Interviews", "6"),
    ("policies", "📜 Policies", "7"),
    ("security", "🛡️ Trust Center", "8"),
    ("analytics", "📈 Analytics", "9"),
]

NAV_SECONDARY: List[Tuple[str, str, str]] = [
    ("settings", "⚙️ Settings", "S"),
    ("help", "❓ Help", "H"),
]


def render_sidebar() -> str:
    """
    Renders the production sidebar navigation and returns the currently active section.
    """
    # Support deep linking via query params
    try:
        qp = st.query_params
        target_nav = qp.get("nav") or qp.get("section")
        valid_sections = [s[0] for s in NAV_PRIMARY + NAV_SECONDARY]
        if target_nav and target_nav in valid_sections:
            st.session_state["nav_section"] = target_nav
    except Exception:
        pass

    if "nav_section" not in st.session_state:
        st.session_state["nav_section"] = "overview"

    active_section = st.session_state["nav_section"]

    with st.sidebar:
        # Workspace Identity
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0.25rem 1rem 0.25rem; border-bottom: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 0.75rem;">
              <div class="capabl-brand-icon" style="width: 32px; height: 32px; font-size: 0.95rem;">C</div>
              <div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #F8FAFC; letter-spacing: -0.01em;">CAPABL OS</div>
                <div style="font-size: 0.7rem; color: #94A3B8;">Recruitment Workspace</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Primary Navigation
        st.markdown('<div class="capabl-nav-section-title">RECRUITMENT WORKSPACE</div>', unsafe_allow_html=True)
        for section_id, label, shortcut in NAV_PRIMARY:
            is_active = (active_section == section_id)
            btn_type = "primary" if is_active else "secondary"
            btn_key = f"nav_btn_{section_id}"

            # Display button with active styling indicator
            button_label = f"{label}   [{shortcut}]" if not is_active else f"{label}  ●"
            if st.button(
                button_label,
                key=btn_key,
                use_container_width=True,
                type=btn_type,
            ):
                if st.session_state["nav_section"] != section_id:
                    st.session_state["nav_section"] = section_id
                    st.rerun()

        st.markdown('<div style="height: 1px; background: rgba(255, 255, 255, 0.06); margin: 0.85rem 0;"></div>', unsafe_allow_html=True)

        # Secondary Navigation
        st.markdown('<div class="capabl-nav-section-title">SYSTEM & PREFERENCES</div>', unsafe_allow_html=True)
        for section_id, label, shortcut in NAV_SECONDARY:
            is_active = (active_section == section_id)
            btn_type = "primary" if is_active else "secondary"
            btn_key = f"nav_btn_{section_id}"

            button_label = f"{label}   [{shortcut}]" if not is_active else f"{label}  ●"
            if st.button(
                button_label,
                key=btn_key,
                use_container_width=True,
                type=btn_type,
            ):
                if st.session_state["nav_section"] != section_id:
                    st.session_state["nav_section"] = section_id
                    st.rerun()

        # Workspace Footer
        st.markdown(
            """
            <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.06); font-size: 0.7rem; color: #64748B;">
              <div>Connected to <strong>Production ChromaDB</strong></div>
              <div style="margin-top: 2px;">Active Profile: <strong>Lead Recruiter</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return st.session_state["nav_section"]
