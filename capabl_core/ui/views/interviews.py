"""
Production Interview Operations Workspace for CAPABL Recruitment Intelligence OS.

Phase 9: Interview Operations.
Implements:
1. Multi-View Real Scheduling Calendar:
   - Day View: Hour-by-hour chronological schedule for selected date.
   - Week View: Multi-day grid grouping available slots and confirmed bookings.
   - Agenda View: Unified chronological listing of all interview commitments.
   - Data powered strictly by MockCalendarService (Asia/Kolkata standard).
2. Enterprise Interview Cards:
   - Displays: candidate, role, interviewer, date, time, duration, and status.
   - Semantic visual distinction for available vs confirmed booked interviews.
3. 5-Stage Animated Booking Flow:
   - Calendar Slot → Interview Preview → Confirmation Modal → Booking → Success State.
   - Animated progress rail with glowing stage indicators.
4. Consequential Action Security Gatekeeper:
   - Explicit user confirmation is strictly mandatory.
   - Final booking execution strictly preserves confirmed=True.
   - Audit event logging on blocked unconfirmed attempts.
5. Success State:
   - "Interview scheduled" confirmation banner with subtle calendar/check animation.
6. Stale Slot & Double-Booking Protection:
   - Stale slot animation (capablSlotFadeOut) on invalid/already booked slots.
   - "That slot is no longer available."
   - Immediate automatic refresh of real available slots. Zero fabricated bookings.
"""

import time
import html
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Dict, Any, List, Optional
import streamlit as st

from capabl_core.calendar.service import DEFAULT_CALENDAR_SERVICE
from capabl_core.calendar.models import InterviewSlot, InterviewBooking, BookingResult
from enhancement.security.audit_logger import DEFAULT_AUDIT_LOGGER

logger = logging.getLogger(__name__)


def format_slot_datetime(dt_obj: datetime) -> Dict[str, str]:
    """Helper formatting datetime into date, time, and display labels."""
    return {
        "date_str": dt_obj.strftime("%Y-%m-%d"),
        "date_label": dt_obj.strftime("%A, %d %B %Y"),
        "time_label": dt_obj.strftime("%I:%M %p"),
        "full_display": dt_obj.strftime("%A, %d %B %Y %I:%M %p"),
    }


def render_booking_flow_progress(active_step: int = 1) -> None:
    """
    Renders the 5-stage animated booking flow visualizer:
    1. Calendar Slot → 2. Interview Preview → 3. Confirmation Modal → 4. Booking → 5. Success State.
    """
    flow_steps = [
        ("Calendar Slot", "📅"),
        ("Interview Preview", "👁️"),
        ("Confirmation Modal", "⚠️"),
        ("Booking Execution", "⚡"),
        ("Success State", "🎉"),
    ]

    st.markdown(
        """
        <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
            Booking Gatekeeper Authorization Flow
        </div>
        """,
        unsafe_allow_html=True,
    )

    flow_html = '<div class="capabl-booking-flow-container">'
    for idx, (label, icon) in enumerate(flow_steps, start=1):
        if idx < active_step:
            step_class = "capabl-booking-step capabl-booking-step-done"
            indicator = "✓"
        elif idx == active_step:
            step_class = "capabl-booking-step capabl-booking-step-active"
            indicator = "●"
        else:
            step_class = "capabl-booking-step"
            indicator = "○"

        flow_html += f"""
        <div class="{step_class}">
            <span style="font-family: monospace; font-size: 0.75rem;">{icon} {indicator} Step {idx}:</span>
            <span>{label}</span>
        </div>
        """
        if idx < len(flow_steps):
            flow_html += '<span style="color: #475569; font-size: 0.8rem;">→</span>'

    flow_html += '</div>'
    st.markdown(flow_html, unsafe_allow_html=True)


def render_interview_card(
    item: Dict[str, Any],
    is_booked: bool = False,
    on_select_slot: Optional[Any] = None,
) -> None:
    """
    Renders an enterprise interview card displaying:
    candidate, role, interviewer, date, time, duration, and status.
    """
    slot_id = item.get("slot_id", "slot_unknown")
    cand_id = item.get("candidate_id", "Unassigned")
    job_id = item.get("job_id", "General Requisition")
    interviewer = item.get("interviewer_name", "Lead Interviewer")
    interviewer_role = item.get("interviewer_role", "Engineering Panel")
    duration = item.get("duration_minutes", 30)
    display_time = item.get("display_time", "")
    timezone_str = item.get("timezone", "Asia/Kolkata")

    card_class = "capabl-interview-card capabl-interview-card-booked" if is_booked else "capabl-interview-card capabl-interview-card-available"
    status_badge = (
        '<span style="background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); padding: 2px 8px; border-radius: 4px; font-size: 0.74rem; font-weight: 700; text-transform: uppercase;">✓ Confirmed Booking</span>'
        if is_booked else
        '<span style="background: rgba(6, 182, 212, 0.12); color: #38BDF8; border: 1px solid rgba(6, 182, 212, 0.4); padding: 2px 8px; border-radius: 4px; font-size: 0.74rem; font-weight: 700; text-transform: uppercase;">● Open Slot</span>'
    )

    st.markdown(
        f"""
        <div class="{card_class} capabl-card-interactive motion-card-enter">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    {status_badge}
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; color: #94A3B8; background: rgba(255, 255, 255, 0.04); padding: 2px 6px; border-radius: 4px;">
                        ID: {html.escape(slot_id)}
                    </span>
                </div>
                <div style="font-size: 0.8rem; font-weight: 600; color: #E2E8F0;">
                    ⏱️ {duration} minutes • Standard Panel
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 0.85rem;">
                <div>
                    <div style="font-size: 0.70rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Candidate</div>
                    <div style="font-size: 0.92rem; font-weight: 700; color: #34D399; margin-top: 1px;">👤 {html.escape(cand_id)}</div>
                </div>
                <div>
                    <div style="font-size: 0.70rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Target Requisition</div>
                    <div style="font-size: 0.92rem; font-weight: 700; color: #38BDF8; margin-top: 1px;">💼 {html.escape(job_id)}</div>
                </div>
                <div>
                    <div style="font-size: 0.70rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Interviewer</div>
                    <div style="font-size: 0.88rem; font-weight: 600; color: #FFFFFF; margin-top: 1px;">
                        🧑‍💼 {html.escape(interviewer)} <span style="font-size: 0.74rem; color: #94A3B8;">({html.escape(interviewer_role)})</span>
                    </div>
                </div>
            </div>

            <div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 0.6rem 0.9rem; font-size: 0.84rem; color: #F1F5F9; display: flex; align-items: center; justify-content: space-between; border-left: 3px solid {'#10B981' if is_booked else '#06B6D4'};">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1rem;">📅</span>
                    <span style="font-size: 0.78rem; color: #94A3B8;">Scheduled:</span>
                    <strong style="color: #FFFFFF; font-family: inherit;">{html.escape(display_time)}</strong>
                </div>
                <span style="font-size: 0.72rem; color: #94A3B8; font-family: 'JetBrains Mono', monospace;">Asia/Kolkata</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_interviews_workspace() -> None:
    """
    Main entry point for CAPABL Phase 9: Interview Operations & Scheduling.
    """
    calendar_service = DEFAULT_CALENDAR_SERVICE

    # Executive Hero Header
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;" class="motion-page-enter">
          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem;">
            <div>
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem;">
                <span style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #6366F1; background: rgba(99, 102, 241, 0.12); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(99, 102, 241, 0.25);">
                  Scheduling Operations
                </span>
                <span style="font-size: 0.75rem; color: #64748B;">• Asia/Kolkata IST Standard</span>
              </div>
              <h2 style="font-size: 1.75rem; font-weight: 800; color: #F8FAFC; margin: 0; letter-spacing: -0.025em;">
                Interview Operations & Calendar
              </h2>
              <div style="font-size: 0.88rem; color: #94A3B8; margin-top: 0.25rem;">
                Timezone-aware scheduling with strict consequential action gatekeeper. State changes require explicit human confirmation.
              </div>
            </div>
            <div style="display: flex; align-items: center; gap: 0.65rem;">
              <span class="capabl-chip capabl-chip-match" style="margin: 0; font-size: 0.75rem; padding: 4px 10px;">
                <span class="capabl-status-dot-active" style="margin-right: 5px;"></span> Gatekeeper Active
              </span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Context resolution
    try:
        from capabl_core.ui.views.candidates import get_candidate_profiles
        from capabl_core.ui.views.jobs import get_job_profiles
        candidates = get_candidate_profiles()
        jobs = get_job_profiles()
        cand_ids = [c["candidate_id"] for c in candidates]
        job_ids = [j["job_id"] for j in jobs]
    except Exception as e:
        logger.warning(f"Error resolving candidates/jobs for filters: {e}")
        cand_ids = []
        job_ids = []

    # Filter Bar
    with st.container():
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.5, 1.5, 1])

        with f_col1:
            sel_candidate = st.selectbox(
                "Filter Candidate:",
                options=["All Candidates"] + cand_ids,
                key="interviews_filter_candidate",
            )

        with f_col2:
            sel_job = st.selectbox(
                "Filter Requisition:",
                options=["All Roles"] + job_ids,
                key="interviews_filter_job",
            )

        with f_col3:
            timezone_str = "Asia/Kolkata"
            st.selectbox(
                "Operating Timezone:",
                options=["Asia/Kolkata (IST)", "UTC", "America/New_York (EST)"],
                index=0,
                key="interviews_tz_selector",
                disabled=True,
                help="CAPABL recruitment calendar standard is strictly synchronized to Asia/Kolkata.",
            )

        with f_col4:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            refresh_clicked = st.button("🔄 Refresh", use_container_width=True, key="btn_refresh_calendar")

    c_filter = None if sel_candidate == "All Candidates" else sel_candidate
    j_filter = None if sel_job == "All Roles" else sel_job

    # Fetch Real Slots & Bookings
    search_res = calendar_service.search_slots(
        candidate_id=c_filter,
        job_id=j_filter,
        timezone_str="Asia/Kolkata",
    )
    available_slots = search_res.slots

    # Real confirmed bookings from calendar service
    confirmed_bookings = []
    for slot_id, booking in calendar_service._bookings.items():
        if c_filter and booking.candidate_id.lower() != c_filter.lower():
            continue
        if j_filter and booking.job_id.lower() != j_filter.lower():
            continue

        slot_ref = calendar_service.get_slot(slot_id)
        interviewer_name = slot_ref.interviewer_name if slot_ref else "Interviewer"
        interviewer_role = slot_ref.interviewer_role if slot_ref else "Recruitment Panel"
        duration = slot_ref.duration_minutes if slot_ref else 30

        start_local = booking.start_time.astimezone(ZoneInfo("Asia/Kolkata"))
        end_local = booking.end_time.astimezone(ZoneInfo("Asia/Kolkata"))
        display_time = f"{start_local.strftime('%A, %d %B %Y %I:%M %p')} - {end_local.strftime('%I:%M %p')} Asia/Kolkata"

        confirmed_bookings.append({
            "slot_id": slot_id,
            "booking_id": booking.booking_id,
            "candidate_id": booking.candidate_id,
            "job_id": booking.job_id,
            "start_time": start_local.isoformat(),
            "end_time": end_local.isoformat(),
            "display_time": display_time,
            "timezone": "Asia/Kolkata",
            "duration_minutes": duration,
            "status": "confirmed",
            "interviewer_name": interviewer_name,
            "interviewer_role": interviewer_role,
            "notes": booking.notes,
        })

    # Calendar View Tabs: Day, Week, Agenda, Availability
    view_tab_day, view_tab_week, view_tab_agenda, view_tab_avail = st.tabs([
        "📅 Day View",
        "🗓️ Week View",
        "📋 Agenda View",
        "➕ Availability",
    ])

    # =========================================================================
    # 0. AVAILABILITY MANAGEMENT (Recruiter-Managed Slots)
    # =========================================================================
    with view_tab_avail:
        st.markdown("#### Manage Interview Availability")
        st.markdown(
            """
            <div style="font-size: 0.84rem; color: #94A3B8; margin-bottom: 1rem;">
                Add available interview time slots for interviewers. Slots become searchable and bookable through the scheduling system.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- Add Available Slot Form ---
        with st.expander("➕ Add Available Interview Slot", expanded=True):
            av_col1, av_col2 = st.columns(2)

            with av_col1:
                from datetime import date as date_cls, timedelta
                today = date_cls.today()
                avail_date = st.date_input(
                    "Interview Date",
                    value=today,
                    min_value=today,
                    max_value=today + timedelta(days=90),
                    key="avail_slot_date",
                )
                avail_start = st.time_input(
                    "Start Time",
                    value=datetime(2026, 1, 1, 10, 0).time(),
                    key="avail_slot_start",
                    step=timedelta(minutes=15),
                )
                avail_end = st.time_input(
                    "End Time",
                    value=datetime(2026, 1, 1, 10, 30).time(),
                    key="avail_slot_end",
                    step=timedelta(minutes=15),
                )

            with av_col2:
                known_interviewers = [
                    "Vikram Malhotra",
                    "Sneha Rao",
                    "Priya Sharma",
                    "Rajesh Kumar",
                    "Arjun Patel",
                ]
                avail_interviewer = st.selectbox(
                    "Interviewer",
                    options=known_interviewers,
                    key="avail_slot_interviewer",
                )
                avail_role = st.text_input(
                    "Interviewer Role",
                    value="Engineering Director",
                    key="avail_slot_role",
                )
                avail_type = st.selectbox(
                    "Interview Type (optional)",
                    options=["Technical Screen", "System Design", "Behavioral", "Culture Fit", "Final Round", "General"],
                    key="avail_slot_type",
                )

            # Candidate/Job assignment (optional)
            av_col3, av_col4 = st.columns(2)
            with av_col3:
                avail_cand = st.selectbox(
                    "Assign Candidate (optional)",
                    options=["Open / Unassigned"] + cand_ids,
                    key="avail_slot_cand",
                )
            with av_col4:
                avail_job = st.selectbox(
                    "Assign Requisition (optional)",
                    options=["General"] + job_ids,
                    key="avail_slot_job",
                )

            if st.button("✅ Create Available Slot", type="primary", key="btn_create_avail_slot"):
                date_str = avail_date.strftime("%Y-%m-%d")
                start_str = avail_start.strftime("%H:%M")
                end_str = avail_end.strftime("%H:%M")
                cand_val = "" if avail_cand == "Open / Unassigned" else avail_cand
                job_val = "" if avail_job == "General" else avail_job

                result = calendar_service.add_slot(
                    date_str=date_str,
                    start_time_str=start_str,
                    end_time_str=end_str,
                    interviewer_name=avail_interviewer,
                    interviewer_role=avail_role,
                    candidate_id=cand_val,
                    job_id=job_val,
                    timezone_str="Asia/Kolkata",
                )

                if result["status"] == "success":
                    # Audit log
                    DEFAULT_AUDIT_LOGGER.log_event(
                        event="interview_availability_added",
                        status="success",
                        payload={
                            "slot_id": result.get("slot_id"),
                            "interviewer": avail_interviewer,
                            "date": date_str,
                            "time": f"{start_str}-{end_str}",
                            "interview_type": avail_type,
                        },
                    )
                    st.success(f"✅ {result['message']}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")

        # --- Current Availability Table ---
        st.markdown("#### Current Interview Slots")
        all_slots = calendar_service.get_all_slots()

        if not all_slots:
            st.info("No interview slots configured. Use the form above to add availability.")
        else:
            # Status counts
            avail_count = sum(1 for s in all_slots if s["status"] == "available")
            booked_count = sum(1 for s in all_slots if s["status"] == "booked")
            st.markdown(
                f"""
                <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                    <span class="capabl-chip capabl-chip-match" style="font-size: 0.75rem; padding: 4px 10px;">
                        ● {avail_count} Available
                    </span>
                    <span class="capabl-chip capabl-chip-strong" style="font-size: 0.75rem; padding: 4px 10px;">
                        ✓ {booked_count} Booked
                    </span>
                    <span style="font-size: 0.75rem; color: #64748B; padding: 4px 10px;">
                        Total: {len(all_slots)} slots
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for slot_info in all_slots:
                is_booked = slot_info["status"] == "booked"
                status_color = "#10B981" if is_booked else "#06B6D4"
                status_bg = "rgba(16, 185, 129, 0.12)" if is_booked else "rgba(6, 182, 212, 0.08)"
                status_label = "✓ Booked" if is_booked else "● Available"
                cand_display = slot_info["candidate_id"] if slot_info["candidate_id"] != "unassigned" else "Open"

                st.markdown(
                    f"""
                    <div style="background: {status_bg}; border: 1px solid {status_color}40; border-radius: 8px;
                                padding: 0.65rem 1rem; margin-bottom: 0.5rem; display: flex; align-items: center;
                                justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;"
                         class="motion-card-enter">
                        <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
                            <span style="font-weight: 700; color: {status_color}; font-size: 0.8rem; min-width: 80px;">
                                {status_label}
                            </span>
                            <span style="font-size: 0.84rem; color: #F1F5F9; font-weight: 600;">
                                📅 {html.escape(slot_info['date_label'])}
                            </span>
                            <span style="font-size: 0.84rem; color: #E2E8F0;">
                                🕐 {html.escape(slot_info['time_label'])}
                            </span>
                            <span style="font-size: 0.82rem; color: #94A3B8;">
                                🧑‍💼 {html.escape(slot_info['interviewer_name'])}
                            </span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <span style="font-size: 0.72rem; color: #64748B; font-family: monospace;">
                                {html.escape(slot_info['slot_id'])} • 👤 {html.escape(cand_display)}
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # =========================================================================
    # 1. DAY VIEW
    # =========================================================================
    with view_tab_day:
        st.markdown("#### Chronological Day Schedule")
        target_dates = ["2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02"]
        selected_date = st.selectbox("Select Schedule Date:", options=target_dates, key="sel_day_view_date")

        day_available = [s for s in available_slots if s["start_time"].startswith(selected_date)]
        day_booked = [b for b in confirmed_bookings if b["start_time"].startswith(selected_date)]

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.markdown(f"##### Available Slots ({len(day_available)})")
            if not day_available:
                st.info(f"No open slots on {selected_date}.")
            else:
                for slot in day_available:
                    render_interview_card(slot, is_booked=False)

        with d_col2:
            st.markdown(f"##### Confirmed Bookings ({len(day_booked)})")
            if not day_booked:
                st.info(f"No confirmed interviews scheduled for {selected_date}.")
            else:
                for book in day_booked:
                    render_interview_card(book, is_booked=True)

    # =========================================================================
    # 2. WEEK VIEW
    # =========================================================================
    with view_tab_week:
        st.markdown("#### Weekly Multi-Day Operational View")
        week_days = [
            ("Tuesday", "2026-09-29"),
            ("Wednesday", "2026-09-30"),
            ("Thursday", "2026-10-01"),
            ("Friday", "2026-10-02"),
        ]

        w_cols = st.columns(len(week_days))
        for idx, (day_name, day_date) in enumerate(week_days):
            with w_cols[idx]:
                st.markdown(
                    f"""
                    <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 0.5rem; text-align: center; margin-bottom: 0.75rem;">
                        <div style="font-size: 0.78rem; font-weight: 700; color: #38BDF8;">{day_name}</div>
                        <div style="font-size: 0.70rem; color: #94A3B8; font-family: monospace;">{day_date}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                w_avail = [s for s in available_slots if s["start_time"].startswith(day_date)]
                w_book = [b for b in confirmed_bookings if b["start_time"].startswith(day_date)]

                for b in w_book:
                    st.markdown(
                        f"""
                        <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.5); border-radius: 6px; padding: 0.45rem; margin-bottom: 0.45rem; font-size: 0.75rem;">
                            <div style="font-weight: 700; color: #34D399;">✓ Booked</div>
                            <div style="color: #FFFFFF;">👤 {html.escape(b['candidate_id'])}</div>
                            <div style="color: #94A3B8; font-size: 0.70rem;">{b['display_time'].split(' ')[3]}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                for a in w_avail:
                    st.markdown(
                        f"""
                        <div style="background: rgba(6, 182, 212, 0.08); border: 1px solid rgba(6, 182, 212, 0.35); border-radius: 6px; padding: 0.45rem; margin-bottom: 0.45rem; font-size: 0.75rem;">
                            <div style="font-weight: 700; color: #38BDF8;">● Available</div>
                            <div style="color: #FFFFFF;">👤 {html.escape(a['candidate_id'])}</div>
                            <div style="color: #94A3B8; font-size: 0.70rem;">{a['display_time'].split(' ')[3]}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # =========================================================================
    # 3. AGENDA VIEW
    # =========================================================================
    with view_tab_agenda:
        st.markdown("#### Chronological Interview Agenda")
        all_agenda = sorted(
            [{"type": "booking", **b} for b in confirmed_bookings] +
            [{"type": "available", **s} for s in available_slots],
            key=lambda x: x["start_time"]
        )

        if not all_agenda:
            st.info("No schedule events found matching current criteria.")
        else:
            for item in all_agenda:
                render_interview_card(item, is_booked=(item["type"] == "booking"))

    # -------------------------------------------------------------------------
    # 4. BOOKING FLOW & CONFIRMATION SURFACE (GATEKEEPER)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### Interactive Booking Flow & Authorization Surface")

    if not available_slots:
        st.warning("No available slots open for booking under current filters.")
        return

    slot_map = {
        f"{s['slot_id']} | {s['display_time']} | {s['interviewer_name']} ({s['candidate_id']})": s
        for s in available_slots
    }

    step_stage = 1
    selected_label = st.selectbox(
        "Select Slot from Calendar to Initialize Booking:",
        options=list(slot_map.keys()),
        key="booking_flow_slot_picker",
    )
    target_slot = slot_map[selected_label]
    step_stage = 2

    # Render Active Progress
    render_booking_flow_progress(active_step=step_stage)

    # Confirmation Surface / Modal Box
    with st.container():
        st.markdown(
            f"""
            <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(6, 182, 212, 0.4); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem;">
                <div style="font-size: 0.88rem; font-weight: 700; color: #38BDF8; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                    <span>⚠️ Consequential State Change • Interview Booking Preview</span>
                </div>
                <div style="font-size: 0.82rem; color: #94A3B8; margin-bottom: 0.75rem;">
                    You are preparing to reserve a calendar interview slot. State mutation is guarded by an authorization gatekeeper.
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; font-size: 0.82rem;">
                    <div><strong>Slot ID:</strong> <code style="color: #38BDF8;">{target_slot['slot_id']}</code></div>
                    <div><strong>Candidate:</strong> <code style="color: #34D399;">{target_slot['candidate_id']}</code></div>
                    <div><strong>Requisition:</strong> <code style="color: #E2E8F0;">{target_slot['job_id']}</code></div>
                    <div><strong>Interviewer:</strong> {target_slot['interviewer_name']} ({target_slot['interviewer_role']})</div>
                    <div><strong>Meeting Duration:</strong> {target_slot['duration_minutes']} minutes</div>
                    <div><strong>Scheduled Time:</strong> {target_slot['display_time']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        confirm_box = st.checkbox(
            f"I explicitly confirm booking interview slot '{target_slot['slot_id']}' for {target_slot['candidate_id']}.",
            value=False,
            key="chk_interview_gatekeeper_confirm",
            help="Confirmation is mandatory. Unconfirmed requests are blocked by the safety gatekeeper.",
        )

        notes_input = st.text_input(
            "Recruiter Notes / Meeting Purpose:",
            value="Technical Evaluation & Architecture Screening",
            key="input_interview_notes",
        )

        if st.button("🚀 Confirm & Book Interview Slot", type="primary", key="btn_execute_interview_booking"):
            # Check Stale State Before Booking
            slot_check = calendar_service.get_slot(target_slot["slot_id"])
            if not slot_check or slot_check.status != "available":
                # Stale Slot Handling
                st.markdown(
                    """
                    <div class="capabl-stale-slot">
                        <strong>⚠️ That slot is no longer available.</strong>
                        <div style="font-size: 0.78rem; margin-top: 0.25rem;">
                            The selected interview slot has already been booked or invalidated. Calendar has been refreshed.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.rerun()

            if not confirm_box:
                # GATEKEEPER STRICT ENFORCEMENT
                st.error(
                    "🛑 **GATEKEEPER BLOCKED**: Interview booking requires explicit user confirmation (`confirmed=True`). "
                    "State mutation was aborted to prevent unauthorized calendar changes."
                )
                DEFAULT_AUDIT_LOGGER.log_event(
                    event="booking_blocked_unconfirmed",
                    status="blocked",
                    payload={
                        "candidate_id": target_slot["candidate_id"],
                        "slot_id": target_slot["slot_id"],
                        "reason": "CONFIRMATION_REQUIRED",
                    },
                )
            else:
                # PRESERVE confirmed=True
                with st.spinner("Executing interview booking past authorization gatekeeper..."):
                    booking_res: BookingResult = calendar_service.book_slot(
                        slot_id=target_slot["slot_id"],
                        candidate_id=target_slot["candidate_id"],
                        job_id=target_slot["job_id"],
                        confirmed=True,
                        notes=notes_input,
                    )

                if booking_res.status == "success":
                    st.session_state["recent_booking_result"] = booking_res
                    st.rerun()
                elif booking_res.status in ("already_booked", "invalid_slot"):
                    st.markdown(
                        """
                        <div class="capabl-stale-slot">
                            <strong>⚠️ That slot is no longer available.</strong>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.error(f"❌ Booking failed: {booking_res.message}")

    # Success Celebration State
    recent_booking: Optional[BookingResult] = st.session_state.get("recent_booking_result")
    if recent_booking and recent_booking.booking:
        b_data = recent_booking.booking if isinstance(recent_booking.booking, dict) else recent_booking.booking.model_dump()
        st.markdown(
            f"""
            <div class="capabl-success-banner">
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.6rem;">🎉</span>
                    <div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">
                            Interview scheduled
                        </div>
                        <div style="font-size: 0.82rem; color: #34D399; font-family: monospace;">
                            Booking ID: {b_data.get('booking_id')} • Status: Confirmed
                        </div>
                    </div>
                </div>
                <div style="font-size: 0.88rem; color: #E2E8F0; line-height: 1.6; margin-top: 0.5rem;">
                    {recent_booking.message}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
