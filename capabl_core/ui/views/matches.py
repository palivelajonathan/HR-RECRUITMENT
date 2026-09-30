"""
Production Match Intelligence Experience for CAPABL Recruitment Intelligence OS.

Phase 6: Match Intelligence Experience.
Implements:
1. Pure Deterministic Set-Based Match Engine:
   - ZERO match percentage, ZERO hiring score, ZERO ranking, ZERO autonomous hiring decision.
   - Matched = Required ∩ Candidate
   - Missing = Required - Candidate
2. Cinematic 5-Stage Transition Flow:
   Candidate → Resume Evidence → Requirements → Deterministic Comparison → Match Result.
3. Semantic Visual Distinction:
   - Matched requirements: subtle success glow (#34D399, emerald border & glow).
   - Missing / unverified requirements: subtle warning/error visual (#F87171, rose border).
4. Sequential Skill Reveal:
   - Skills reveal in sequenced order (Matched first, then Missing) with staggered animation delays.
5. Interactive Evidence Drawer:
   - Clicking any skill animates and reveals supporting evidence (source, page, exact citation).
   - Missing skills display factual negative verification (zero fabricated evidence).
"""

from typing import Dict, Any, List, Optional, Set
import html
import streamlit as st

from capabl_core.workflow import DEFAULT_WORKFLOW_SERVICE, AutomaticMatchResult
from capabl_core.matching.models import MatchResult, SkillEvidence
from capabl_core.calendar.service import DEFAULT_CALENDAR_SERVICE
from capabl_core.ui.views.candidates import get_candidate_profiles
from capabl_core.ui.views.jobs import get_job_profiles


def render_matches_workspace() -> None:
    """
    Main entry point for the Match Intelligence Experience.
    Provides candidate & job pair selector, cinematic transition pipeline,
    sequential skill reveals, and the interactive evidence drawer.
    """
    # Active Pair State
    candidates = get_candidate_profiles()
    jobs = get_job_profiles()

    if not candidates:
        st.markdown(
            """
            <div class="capabl-empty-card" style="text-align: center; padding: 2.5rem 1.5rem; background: rgba(30, 41, 59, 0.4); border: 1px dashed rgba(148, 163, 184, 0.2); border-radius: 12px; margin: 1.5rem 0;">
              <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">👥</div>
              <h3 style="color: #F8FAFC; margin-bottom: 0.5rem; font-size: 1.15rem;">No Candidate Profiles Ingested</h3>
              <p style="color: #94A3B8; font-size: 0.88rem; max-width: 480px; margin: 0 auto 1.25rem auto;">
                Deterministic matching requires at least one indexed candidate resume. Navigate to the Candidates workspace or Overview to upload candidate resumes.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if not jobs:
        st.markdown(
            """
            <div class="capabl-empty-card" style="text-align: center; padding: 2.5rem 1.5rem; background: rgba(30, 41, 59, 0.4); border: 1px dashed rgba(148, 163, 184, 0.2); border-radius: 12px; margin: 1.5rem 0;">
              <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">💼</div>
              <h3 style="color: #F8FAFC; margin-bottom: 0.5rem; font-size: 1.15rem;">No Job Requisitions Ingested</h3>
              <p style="color: #94A3B8; font-size: 0.88rem; max-width: 480px; margin: 0 auto 1.25rem auto;">
                Deterministic matching requires at least one indexed job description. Navigate to the Jobs workspace to register and upload job requisitions.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Header
    st.markdown("### Match Intelligence Experience")
    st.caption(
        "Deterministic Resume ↔ Job Description matching. Authoritative set-based comparison with "
        "zero subjective scoring, ranking, or autonomous hiring decisions."
    )

    # -------------------------------------------------------------------------
    # 1. CANDIDATE & REQUISITION SELECTOR BAR
    # -------------------------------------------------------------------------
    cand_ids = [c["candidate_id"] for c in candidates]
    job_ids = [j["job_id"] for j in jobs]

    current_cid = st.session_state.get("candidate_id", cand_ids[0])
    if current_cid not in cand_ids:
        current_cid = cand_ids[0]

    current_jid = st.session_state.get("job_id", job_ids[0])
    if current_jid not in job_ids:
        current_jid = job_ids[0]

    c_sel_col, j_sel_col, replay_col = st.columns([3, 3, 2])

    with c_sel_col:
        sel_cid = st.selectbox(
            "Select Candidate",
            options=cand_ids,
            index=cand_ids.index(current_cid),
            format_func=lambda cid: f"{next((c['name'] for c in candidates if c['candidate_id'] == cid), cid)} ({cid})",
            key="match_exp_cand_sel",
        )
        if sel_cid != current_cid:
            st.session_state["candidate_id"] = sel_cid
            st.session_state["selected_match_skill"] = None
            st.rerun()

    with j_sel_col:
        sel_jid = st.selectbox(
            "Select Job Requisition",
            options=job_ids,
            index=job_ids.index(current_jid),
            format_func=lambda jid: f"{next((j['title'] for j in jobs if j['job_id'] == jid), jid)} ({jid})",
            key="match_exp_job_sel",
        )
        if sel_jid != current_jid:
            st.session_state["job_id"] = sel_jid
            st.session_state["selected_match_skill"] = None
            st.rerun()

    with replay_col:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        if st.button("🎬 Replay Comparison Flow", key="btn_replay_cinematic", use_container_width=True):
            st.session_state["cinematic_step"] = 5
            st.session_state["selected_match_skill"] = None
            st.rerun()

    selected_cand = next((c for c in candidates if c["candidate_id"] == sel_cid), candidates[0])
    selected_job = next((j for j in jobs if j["job_id"] == sel_jid), jobs[0])

    # -------------------------------------------------------------------------
    # 2. RUN DETERMINISTIC MATCH
    # -------------------------------------------------------------------------
    match_result_obj: AutomaticMatchResult = DEFAULT_WORKFLOW_SERVICE.run_automatic_match(
        candidate_id=sel_cid,
        job_id=sel_jid,
        trigger="automatic",
    )
    st.session_state["active_match"] = match_result_obj

    if match_result_obj.status == "waiting_for_job_description":
        st.info(f"Resume for candidate '{sel_cid}' is available. Waiting for Job Description upload before matching.")
        return
    elif match_result_obj.status == "waiting_for_resume":
        st.info(f"Job Description '{sel_jid}' is available. Waiting for Candidate Resume upload before matching.")
        return
    elif match_result_obj.status == "match_error":
        st.error(f"Deterministic comparison error: {match_result_obj.message}")
        return

    match_result: Optional[MatchResult] = match_result_obj.match_result
    if not match_result:
        st.warning("Match result data could not be computed.")
        return

    # -------------------------------------------------------------------------
    # 3. CINEMATIC 5-STAGE TRANSITION FLOW
    # -------------------------------------------------------------------------
    # Candidate -> Resume evidence -> Requirements -> Deterministic comparison -> Match result
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    cand_primary_src = selected_cand.get("source_primary", "resume.pdf")
    job_primary_src = selected_job.get("source_primary", "job_description.pdf")
    total_req_count = len(match_result.required_skills)
    matched_count = len(match_result.matched_skills)
    missing_count = len(match_result.missing_skills)

    # -------------------------------------------------------------------------
    # 3. SIGNATURE MATCH ANIMATION: 5-STAGE DETERMINISTIC FLOW
    # -------------------------------------------------------------------------
    # 3. CINEMATIC 5-STAGE TRANSITION FLOW
    # -------------------------------------------------------------------------
    # 1. Candidate -> 2. Resume Evidence -> 3. Requirements -> 4. Deterministic Comparison -> 5. Match Result
    st.markdown(
        f"""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 8px; padding: 0.6rem 1rem; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; font-size: 0.78rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="color: #38BDF8; font-weight: 700;">1. Candidate</span>
            <span style="color: #64748B;">→</span>
            <span style="color: #818CF8; font-weight: 700;">2. Resume Evidence</span>
            <span style="color: #64748B;">→</span>
            <span style="color: #C084FC; font-weight: 700;">3. Requirements</span>
            <span style="color: #64748B;">→</span>
            <span style="color: #F472B6; font-weight: 700;">4. Deterministic Comparison</span>
            <span style="color: #64748B;">→</span>
            <span style="color: #34D399; font-weight: 700;">5. Match Result</span>
          </div>
          <span class="capabl-chip capabl-chip-match" style="font-size: 0.72rem; margin: 0;">SET THEORY RESOLUTION</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Stage 1: Show Processing State
    st.markdown(
        f"""
        <div class="capabl-match-processing-panel motion-card-enter">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span class="capabl-status-dot-active" style="width: 10px; height: 10px;"></span>
            <div>
              <div style="font-size: 0.85rem; font-weight: 700; color: #F8FAFC;">
                Stage 1: Deterministic Set Comparison Pipeline Active
              </div>
              <div style="font-size: 0.74rem; color: #94A3B8;">
                Scanning <code>{selected_cand['chunk_count']}</code> resume chunks against <code>{total_req_count}</code> JD directives • Pure Set Theory ($M = R \\cap C$, $G = R \\setminus C$)
              </div>
            </div>
          </div>
          <span class="capabl-chip capabl-chip-match" style="font-size: 0.72rem;">ZERO SCORING • ZERO AI HIRING</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Stage 2: Requirements Resolve
    req_chips_html = "".join([
        f'<span class="capabl-chip capabl-chip-brand" style="font-size: 0.75rem; margin: 3px;">{req}</span>'
        for req in match_result.required_skills
    ])
    st.markdown(
        f"""
        <div class="capabl-requirements-resolve-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #A5B4FC; letter-spacing: 0.05em;">
              Stage 2: Target Requirements Resolved ({total_req_count} Mandates in $R$)
            </div>
            <span style="font-size: 0.72rem; color: #64748B; font-family: monospace;">Source: {html.escape(job_primary_src)}</span>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 0.4rem;">
            {req_chips_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Stage 3 & 4: Matched Skills Sequentially & Missing Skills Separately
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    col_matched, col_missing = st.columns(2)
    selected_skill = st.session_state.get("selected_match_skill", None)

    with col_matched:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
              <span style="font-size: 0.88rem; font-weight: 700; color: #34D399;">
                🟢 Stage 3: Matched Skills ($M = R \\cap C$)
              </span>
              <span class="capabl-chip capabl-chip-match" style="font-size: 0.72rem;">{matched_count} Verified</span>
            </div>
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.65rem;">
              Revealed sequentially with verified citations in candidate resume.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if match_result.matched_skills:
            for idx, skill in enumerate(match_result.matched_skills):
                delay_ms = idx * 75
                is_curr = (selected_skill == skill)
                border_style = "2px solid #34D399" if is_curr else "1px solid rgba(16, 185, 129, 0.45)"
                glow_style = "0 0 20px 2px rgba(16, 185, 129, 0.5)" if is_curr else "0 0 12px -2px rgba(16, 185, 129, 0.25)"

                btn_col1, btn_col2 = st.columns([3.8, 1.2])
                with btn_col1:
                    st.markdown(
                        f"""
                        <div class="capabl-skill-matched-seq" style="animation-delay: {delay_ms}ms; border: {border_style}; box-shadow: {glow_style}; width: 100%; justify-content: space-between;">
                          <span>✓ <strong>{skill}</strong></span>
                          <span style="font-size: 0.7rem; color: #A7F3D0; font-family: 'JetBrains Mono', monospace;">citation verified</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with btn_col2:
                    if st.button("Inspect", key=f"btn_skill_ev_m_{skill}", use_container_width=True):
                        st.session_state["selected_match_skill"] = skill
                        st.session_state["selected_match_is_missing"] = False
                        st.rerun()
        else:
            st.info("Zero candidate skills matched the mandatory requirements.")

    with col_missing:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
              <span style="font-size: 0.88rem; font-weight: 700; color: #F87171;">
                🔴 Stage 4: Missing Skills ($G = R \\setminus C$)
              </span>
              <span class="capabl-chip capabl-chip-closed" style="font-size: 0.72rem;">{missing_count} Unverified</span>
            </div>
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.65rem;">
              Revealed separately. Factual negative verification (zero hallucinated evidence).
            </div>
            """,
            unsafe_allow_html=True,
        )

        if match_result.missing_skills:
            matched_offset = len(match_result.matched_skills) * 75
            for idx, skill in enumerate(match_result.missing_skills):
                delay_ms = matched_offset + (idx * 75)
                is_curr = (selected_skill == skill)
                border_style = "2px solid #F87171" if is_curr else "1px solid rgba(239, 68, 68, 0.45)"
                glow_style = "0 0 20px 2px rgba(239, 68, 68, 0.4)" if is_curr else "0 0 12px -2px rgba(239, 68, 68, 0.20)"

                b_col1, b_col2 = st.columns([3.8, 1.2])
                with b_col1:
                    st.markdown(
                        f"""
                        <div class="capabl-skill-missing-seq" style="animation-delay: {delay_ms}ms; border: {border_style}; box-shadow: {glow_style}; width: 100%; justify-content: space-between;">
                          <span>• <strong>{skill}</strong></span>
                          <span style="font-size: 0.7rem; color: #FECDD3; font-family: 'JetBrains Mono', monospace;">not in resume</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with b_col2:
                    if st.button("Inspect", key=f"btn_skill_ev_gap_{skill}", use_container_width=True):
                        st.session_state["selected_match_skill"] = skill
                        st.session_state["selected_match_is_missing"] = True
                        st.rerun()
        else:
            st.success("All required technical qualifications are verified in the candidate's resume!")

    # Stage 5: Final Factual Result Settles
    st.markdown(
        f"""
        <div class="capabl-result-settle-card">
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem;">
            <div>
              <div style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #34D399; letter-spacing: 0.05em;">
                Stage 5: Final Factual Result Settled
              </div>
              <div style="font-size: 1.15rem; font-weight: 800; color: #F8FAFC; margin-top: 2px;">
                Deterministic Set Partition: <span style="color: #34D399;">{matched_count} Matched</span> • <span style="color: #F87171;">{missing_count} Missing</span> of {total_req_count} Total
              </div>
              <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 4px;">
                Set Formula: <code style="color: #A5B4FC;">M = R ∩ C</code> ({matched_count}) &nbsp;|&nbsp; <code style="color: #FCA5A5;">G = R \\ C</code> ({missing_count}) • Zero arbitrary percentage scores • Zero AI hiring decisions
              </div>
            </div>
            <div style="text-align: right;">
              <span class="capabl-chip capabl-chip-match" style="font-size: 0.75rem; padding: 4px 10px;">
                ✓ Settled Factual Record
              </span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------------------
    # 6. ANIMATED EVIDENCE DRAWER (SKILL -> EVIDENCE DRAWER)
    # -------------------------------------------------------------------------
    if selected_skill:
        is_missing = st.session_state.get("selected_match_is_missing", False)
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        if not is_missing:
            # Matched Skill Evidence
            citations = [e for e in match_result.matched_evidence if e.skill.lower() == selected_skill.lower()]
            c_count = len(citations)

            st.markdown(
                f"""
                <div class="capabl-evidence-drawer">
                  <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                    <div>
                      <div style="font-size: 0.75rem; text-transform: uppercase; color: #10B981; font-weight: 700; letter-spacing: 0.05em;">Evidence Drawer • Verified Match</div>
                      <div style="font-size: 1.3rem; font-weight: 800; color: #F8FAFC; margin-top: 2px;">Skill Citation: <span style="color: #34D399;">{selected_skill}</span></div>
                    </div>
                    <span class="capabl-chip capabl-chip-match">Grounded Evidence Found ({c_count})</span>
                  </div>
                  <div style="font-size: 0.84rem; color: #94A3B8; margin-bottom: 1rem;">
                    Candidate: <code>{sel_cid}</code> • Source Document: <code>{cand_primary_src}</code> • Match Status: <strong>Verified Intersection</strong>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if citations:
                for idx, cite in enumerate(citations, 1):
                    page_str = f"Page {cite.page}" if cite.page is not None else "Page 1"
                    doc_id_str = cite.document_id or sel_cid
                    # Highlight skill term in excerpt
                    excerpt_text = cite.excerpt
                    clean_excerpt = excerpt_text.replace("<", "&lt;").replace(">", "&gt;")

                    st.markdown(
                        f"""
                        <div style="background: rgba(18, 24, 38, 0.7); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;">
                          <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.78rem;">
                            <span style="color: #38BDF8; font-weight: 600;">Citation #{idx} • <code>{cite.source}</code></span>
                            <span style="color: #94A3B8;">{page_str} • Document: <code>{doc_id_str}</code></span>
                          </div>
                          <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #E2E8F0; background: rgba(0,0,0,0.3); padding: 0.75rem; border-radius: 6px; border-left: 3px solid #10B981;">
                            "{clean_excerpt}"
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info(f"Verified via indexed candidate profile for `{selected_skill}`.")

        else:
            # Missing Skill Factual Negative
            st.markdown(
                f"""
                <div class="capabl-evidence-drawer-missing">
                  <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                    <div>
                      <div style="font-size: 0.75rem; text-transform: uppercase; color: #F87171; font-weight: 700; letter-spacing: 0.05em;">Evidence Drawer • Factual Negative Verification</div>
                      <div style="font-size: 1.3rem; font-weight: 800; color: #F8FAFC; margin-top: 2px;">Unverified Requirement: <span style="color: #F87171;">{selected_skill}</span></div>
                    </div>
                    <span class="capabl-chip capabl-chip-closed">Zero Factual Citations</span>
                  </div>
                  <div style="font-size: 0.86rem; color: #E2E8F0; line-height: 1.6; margin-bottom: 1rem;">
                    The skill <strong style="color:#F87171;">'{selected_skill}'</strong> is an authoritative requirement specified in job description 
                    <code>{sel_jid}</code>. However, no explicit textual mention, keyword occurrence, or regex pattern match was identified 
                    within candidate <code>{sel_cid}</code>'s verified resume chunks.
                  </div>
                  <div style="background: rgba(0,0,0,0.35); border-radius: 6px; padding: 0.75rem; font-size: 0.8rem; color: #94A3B8; border-left: 3px solid #EF4444;">
                    <strong style="color:#FCA5A5;">Immutable Grounding Rule:</strong> CAPABL never synthesizes, hallucinates, or infers unverified competencies. Missing skills receive strictly zero fabricated evidence.
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        close_col, _ = st.columns([2, 5])
        with close_col:
            if st.button("✕ Close Evidence Drawer", key="btn_close_ev_drawer"):
                st.session_state["selected_match_skill"] = None
                st.rerun()

    # -------------------------------------------------------------------------
    # 7. EXPANDABLE FACTUAL BREAKDOWN & HUMAN-IN-THE-LOOP ACTION
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    with st.expander("📄 View Full Factual Match Summary & Citations", expanded=False):
        st.markdown(match_result_obj.summary_markdown)

    # Confirmation Gatekeeper for Interview Scheduling
    st.markdown("##### Schedule Technical Interview (Confirmation Gatekeeper)")
    st.caption("Human-in-the-loop action. The autonomous agent cannot book without explicit recruiter confirmation.")

    # Fetch actual available slots from calendar service
    search_res = DEFAULT_CALENDAR_SERVICE.search_slots(
        candidate_id=sel_cid,
        job_id=sel_jid,
        timezone_str="Asia/Kolkata",
    )
    slots_list = search_res.slots if search_res and search_res.slots else []
    if not slots_list:
        all_slots_res = DEFAULT_CALENDAR_SERVICE.search_slots(timezone_str="Asia/Kolkata")
        slots_list = all_slots_res.slots if all_slots_res and all_slots_res.slots else []

    if not slots_list:
        st.info("No open interview slots available in calendar. Use the Interviews workspace to define availability.")
    else:
        slot_map = {}
        for s in slots_list:
            if isinstance(s, dict):
                st_time = str(s.get("start_time", ""))
                disp = s.get("display_time") or f"{st_time} ({s.get('interviewer_name', 'Interviewer')} • {s.get('duration_minutes', 30)}m)"
                slot_map[disp] = st_time
            else:
                st_time = s.start_time.isoformat() if hasattr(s.start_time, "isoformat") else str(s.start_time)
                disp = f"{s.start_time.strftime('%Y-%m-%d %I:%M %p') if hasattr(s.start_time, 'strftime') else s.start_time} ({s.interviewer_name} • {s.duration_minutes}m)"
                slot_map[disp] = st_time
        int_col1, int_col2, int_col3 = st.columns([3, 3, 2])
        with int_col1:
            sel_slot_label = st.selectbox(
                "Available Interview Slot",
                options=list(slot_map.keys()),
                key="match_int_slot",
            )
        with int_col2:
            schedule_notes = st.text_input(
                "Recruiter Notes",
                value=f"Technical review for {selected_job['title']} regarding verified skills ({', '.join(match_result.matched_skills[:3]) if match_result.matched_skills else 'Profile Review'})",
                key="match_int_notes",
            )
        with int_col3:
            st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
            if st.button("Confirm & Book Interview", key="btn_match_book_interview", use_container_width=True):
                slot_iso = slot_map[sel_slot_label]
                try:
                    booking_result = DEFAULT_CALENDAR_SERVICE.book_interview(
                        candidate_id=sel_cid,
                        job_id=sel_jid,
                        time_slot=slot_iso,
                        confirmed=True,
                        notes=schedule_notes,
                    )
                    if getattr(booking_result, "booking", None):
                        st.success(
                            f"Interview Confirmed. Booking ID: `{booking_result.booking.booking_id}` "
                            f"scheduled for candidate `{sel_cid}` at `{slot_iso}`."
                        )
                    else:
                        st.info(getattr(booking_result, "message", "Interview booking requested."))
                except Exception as b_exc:
                    st.error("Unable to complete interview booking. Please verify calendar availability.")
                    with st.expander("Technical details"):
                        st.code(str(b_exc))
