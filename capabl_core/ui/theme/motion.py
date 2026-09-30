"""
Centralized Motion System for CAPABL Recruitment Intelligence OS.

Phase 1: Premium Visual Language & Motion System.
Defines reusable CSS animations, spring-like keyframes, micro-interactions,
and accessibility controls respecting 'prefers-reduced-motion'.
"""

from capabl_core.ui.theme.tokens import MOTION


def generate_motion_css() -> str:
    """
    Returns clean CSS definitions for all 17 CAPABL motion primitives
    and micro-interaction system rules.
    """
    return f"""
/* =============================================================================
   CAPABL MOTION ENGINE & TRANSITIONS SYSTEM
   ============================================================================= */

:root {{
  --capabl-ease-spring: {MOTION.EASE_SPRING};
  --capabl-ease-smooth: {MOTION.EASE_SMOOTH_OUT};
  --capabl-ease-sharp: {MOTION.EASE_SHARP};
  --capabl-dur-instant: {MOTION.DURATION_INSTANT};
  --capabl-dur-fast: {MOTION.DURATION_FAST};
  --capabl-dur-standard: {MOTION.DURATION_STANDARD};
  --capabl-dur-complex: {MOTION.DURATION_COMPLEX};
  --capabl-dur-long: {MOTION.DURATION_LONG};
}}

/* -----------------------------------------------------------------------------
   1. KEYFRAME PRIMITIVES
   ----------------------------------------------------------------------------- */

/* 1. Page Enter / Exit */
@keyframes capablPageEnter {{
  from {{
    opacity: 0;
    transform: translateY(12px) scale(0.995);
  }}
  to {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
}}

@keyframes capablPageExit {{
  from {{
    opacity: 1;
    transform: translateY(0);
  }}
  to {{
    opacity: 0;
    transform: translateY(-8px);
  }}
}}

/* 3. Card Enter */
@keyframes capablCardEnter {{
  from {{
    opacity: 0;
    transform: translateY(16px);
  }}
  to {{
    opacity: 1;
    transform: translateY(0);
  }}
}}

/* 5. Modal Enter */
@keyframes capablModalEnter {{
  from {{
    opacity: 0;
    transform: scale(0.95) translateY(12px);
  }}
  to {{
    opacity: 1;
    transform: scale(1) translateY(0);
  }}
}}

/* 6. Drawer Enter */
@keyframes capablDrawerEnter {{
  from {{
    opacity: 0;
    transform: translateX(-24px);
  }}
  to {{
    opacity: 1;
    transform: translateX(0);
  }}
}}

/* 7. Tooltip Pop */
@keyframes capablTooltipPop {{
  from {{
    opacity: 0;
    transform: scale(0.92) translateY(4px);
  }}
  to {{
    opacity: 1;
    transform: scale(1) translateY(0);
  }}
}}

/* 10. Skeleton Loader Shimmer */
@keyframes capablShimmer {{
  0% {{
    background-position: -200% 0;
  }}
  100% {{
    background-position: 200% 0;
  }}
}}

/* 11. Controlled Success Confirmation */
@keyframes capablSuccessGlow {{
  0% {{
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
    border-color: rgba(16, 185, 129, 0.4);
  }}
  50% {{
    box-shadow: 0 0 24px 4px rgba(16, 185, 129, 0.25);
    border-color: rgba(16, 185, 129, 0.8);
  }}
  100% {{
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
    border-color: rgba(16, 185, 129, 0.3);
  }}
}}

/* 12. Restrained Error Attention */
@keyframes capablErrorAttention {{
  0%, 100% {{
    transform: translateX(0);
  }}
  20%, 60% {{
    transform: translateX(-4px);
  }}
  40%, 80% {{
    transform: translateX(4px);
  }}
}}

/* 13. Subtle Status Pulse (Operational Breathing) */
@keyframes capablStatusPulse {{
  0% {{
    transform: scale(0.95);
    opacity: 0.85;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.45);
  }}
  70% {{
    transform: scale(1.05);
    opacity: 1;
    box-shadow: 0 0 10px 4px rgba(16, 185, 129, 0);
  }}
  100% {{
    transform: scale(0.95);
    opacity: 0.85;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
  }}
}}

/* 15. Evidence Reveal (Staggered Unfold) */
@keyframes capablEvidenceReveal {{
  from {{
    opacity: 0;
    transform: translateY(14px) scale(0.98);
  }}
  to {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
}}

/* 16. Agent Cognitive Activity Pulse */
@keyframes capablAgentPulse {{
  0%, 100% {{
    border-color: rgba(99, 102, 241, 0.3);
    box-shadow: 0 0 16px -2px rgba(99, 102, 241, 0.15);
  }}
  50% {{
    border-color: rgba(6, 182, 212, 0.6);
    box-shadow: 0 0 24px 2px rgba(6, 182, 212, 0.28);
  }}
}}

/* 17. Metric Card Number Counter Pop */
@keyframes capablCountPop {{
  0% {{
    transform: scale(0.65);
    opacity: 0;
  }}
  65% {{
    transform: scale(1.08);
  }}
  100% {{
    transform: scale(1);
    opacity: 1;
  }}
}}

/* 18. Document Extraction Scanner Beam */
@keyframes capablScanLine {{
  0% {{
    top: 0%;
    opacity: 0.2;
  }}
  50% {{
    opacity: 1;
  }}
  100% {{
    top: 100%;
    opacity: 0.2;
  }}
}}

/* -----------------------------------------------------------------------------
   2. REUSABLE ANIMATION CLASSES
   ----------------------------------------------------------------------------- */

.motion-page-enter {{
  animation: capablPageEnter var(--capabl-dur-complex) var(--capabl-ease-spring) forwards;
}}

.motion-card-enter {{
  animation: capablCardEnter var(--capabl-dur-standard) var(--capabl-ease-spring) both;
}}

.motion-modal-enter {{
  animation: capablModalEnter var(--capabl-dur-standard) var(--capabl-ease-spring) forwards;
}}

.motion-drawer-enter {{
  animation: capablDrawerEnter var(--capabl-dur-standard) var(--capabl-ease-spring) forwards;
}}

.motion-evidence-reveal {{
  animation: capablEvidenceReveal var(--capabl-dur-standard) var(--capabl-ease-spring) both;
}}

.motion-agent-active {{
  animation: capablAgentPulse 2.8s ease-in-out infinite;
}}

.motion-success-flash {{
  animation: capablSuccessGlow 0.9s var(--capabl-ease-smooth) forwards;
}}

.motion-error-shake {{
  animation: capablErrorAttention 0.4s var(--capabl-ease-sharp) forwards;
}}

/* 19. Requirement Chip Stagger Entrance */
@keyframes capablChipFadeIn {{
  from {{
    opacity: 0;
    transform: translateY(8px) scale(0.92);
  }}
  to {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
}}

/* 20. Sequential Skill Reveal */
@keyframes capablSkillSequentialReveal {{
  0% {{
    opacity: 0;
    transform: translateY(12px) scale(0.88);
  }}
  70% {{
    opacity: 1;
    transform: translateY(-2px) scale(1.03);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
}}

/* 21. Evidence Drawer Slide Entrance */
@keyframes capablDrawerSlide {{
  0% {{
    opacity: 0;
    transform: translateY(16px) scale(0.98);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
}}

/* 22. Cinematic Pipeline Step Pulse */
@keyframes capablPipelinePulse {{
  0%, 100% {{
    box-shadow: 0 0 12px -2px rgba(6, 182, 212, 0.25);
    border-color: rgba(6, 182, 212, 0.4);
  }}
  50% {{
    box-shadow: 0 0 24px 2px rgba(6, 182, 212, 0.55);
    border-color: rgba(6, 182, 212, 0.85);
  }}
}}

/* 23. Evidence Graph Flow Pulse */
@keyframes capablFlowPulse {{
  from {{
    stroke-dashoffset: 40;
  }}
  to {{
    stroke-dashoffset: 0;
  }}
}}

/* 24. Evidence Card Metadata Slide-In */
@keyframes capablCardExpand {{
  0% {{
    opacity: 0;
    transform: translateY(8px);
    max-height: 0;
  }}
  100% {{
    opacity: 1;
    transform: translateY(0);
    max-height: 1200px;
  }}
}}

/* 25. Evidence Query Keyword Highlight Pulse */
@keyframes capablHighlightPulse {{
  0%, 100% {{
    background-color: rgba(245, 158, 11, 0.22);
    border-color: rgba(245, 158, 11, 0.5);
  }}
  50% {{
    background-color: rgba(245, 158, 11, 0.42);
    border-color: rgba(245, 158, 11, 0.9);
  }}
}}

/* 26. Loading Stage Step Pulse */
@keyframes capablLoadingPulse {{
  0%, 100% {{
    opacity: 0.6;
    transform: scale(0.98);
  }}
  50% {{
    opacity: 1;
    transform: scale(1.02);
  }}
}}

/* 27. Chat Message Slide-In */
@keyframes capablMessageSlideIn {{
  0% {{
    opacity: 0;
    transform: translateY(10px) scale(0.98);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
}}

/* 28. Activity Rail Line Flow Pulse */
@keyframes capablActivityLinePulse {{
  0%, 100% {{
    opacity: 0.35;
    background-position: 0% 0%;
  }}
  50% {{
    opacity: 0.95;
    background-position: 0% 100%;
  }}
}}

/* 29. Send Button Micro-interaction */
@keyframes capablButtonSend {{
  0% {{
    transform: scale(1);
  }}
  50% {{
    transform: scale(0.92);
  }}
  100% {{
    transform: scale(1);
  }}
}}

/* 30. Calendar Success Check Animation */
@keyframes capablCalendarCheck {{
  0% {{
    transform: scale(0.75) rotate(-10deg);
    opacity: 0;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6);
  }}
  60% {{
    transform: scale(1.08) rotate(2deg);
    opacity: 1;
    box-shadow: 0 0 28px 6px rgba(16, 185, 129, 0.45);
  }}
  100% {{
    transform: scale(1) rotate(0deg);
    opacity: 1;
    box-shadow: 0 0 16px 2px rgba(16, 185, 129, 0.25);
  }}
}}

/* 31. Booking Flow Stage Pulse */
@keyframes capablBookingStagePulse {{
  0%, 100% {{
    box-shadow: 0 0 10px -2px rgba(6, 182, 212, 0.3);
    border-color: rgba(6, 182, 212, 0.4);
  }}
  50% {{
    box-shadow: 0 0 24px 3px rgba(6, 182, 212, 0.6);
    border-color: rgba(6, 182, 212, 0.9);
  }}
}}

/* 32. Stale Slot Fade Out */
@keyframes capablSlotFadeOut {{
  0% {{
    opacity: 1;
    transform: scale(1);
    max-height: 120px;
  }}
  50% {{
    opacity: 0.4;
    border-color: rgba(239, 68, 68, 0.6);
  }}
  100% {{
    opacity: 0;
    transform: scale(0.95);
    max-height: 0;
    margin: 0;
    padding: 0;
  }}
}}

/* 33. Phase 10: Smooth Policy Section Expand */
@keyframes capablSectionExpand {{
  0% {{
    opacity: 0;
    transform: translateY(-8px);
    max-height: 0;
  }}
  60% {{
    opacity: 0.85;
    transform: translateY(2px);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0);
    max-height: 1200px;
  }}
}}

/* 34. Phase 10: Evidence Citation Reveal */
@keyframes capablCitationReveal {{
  0% {{
    opacity: 0;
    transform: scale(0.92) translateX(-6px);
    box-shadow: 0 0 0 0 rgba(6, 182, 212, 0);
  }}
  70% {{
    opacity: 1;
    transform: scale(1.02) translateX(0);
    box-shadow: 0 0 16px 2px rgba(6, 182, 212, 0.35);
  }}
  100% {{
    opacity: 1;
    transform: scale(1) translateX(0);
    box-shadow: 0 0 8px 1px rgba(6, 182, 212, 0.15);
  }}
}}

/* 35. Phase 10: Policy Card Entrance */
@keyframes capablPolicyCardEnter {{
  0% {{
    opacity: 0;
    transform: translateY(12px) scale(0.98);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
}}

/* 36. Phase 11: Security Shield Pulse & Drawer Reveal */
@keyframes capablSecurityPulse {{
  0%, 100% {{
    box-shadow: 0 0 14px -2px rgba(16, 185, 129, 0.25);
    border-color: rgba(16, 185, 129, 0.4);
  }}
  50% {{
    box-shadow: 0 0 28px 4px rgba(16, 185, 129, 0.55);
    border-color: rgba(16, 185, 129, 0.9);
  }}
}}

@keyframes capablTimelineNodeEnter {{
  0% {{
    opacity: 0;
    transform: translateX(-12px);
  }}
  100% {{
    opacity: 1;
    transform: translateX(0);
  }}
}}

@keyframes capablSecurityDrawerOpen {{
  0% {{
    opacity: 0;
    transform: translateY(16px) scale(0.98);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
}}

@keyframes capablChartEnter {{
  0% {{
    opacity: 0;
    transform: translateY(12px) scale(0.99);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
}}

/* 37. SIGNATURE MATCH ANIMATION: 5-Stage Deterministic Flow */
@keyframes capablMatchProcessPulse {{
  0% {{
    opacity: 0.6;
    border-color: rgba(6, 182, 212, 0.3);
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
  }}
  50% {{
    opacity: 1;
    border-color: rgba(6, 182, 212, 0.8);
    box-shadow: 0 0 24px rgba(6, 182, 212, 0.4);
  }}
  100% {{
    opacity: 0.6;
    border-color: rgba(6, 182, 212, 0.3);
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
  }}
}}

@keyframes capablRequirementsResolve {{
  0% {{
    opacity: 0;
    transform: translateY(14px) scale(0.97);
  }}
  60% {{
    opacity: 0.9;
    transform: translateY(-2px) scale(1.01);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
}}

@keyframes capablSkillMatchedSeq {{
  0% {{
    opacity: 0;
    transform: translateY(12px) scale(0.9);
    border-color: rgba(16, 185, 129, 0.2);
  }}
  70% {{
    opacity: 1;
    transform: translateY(-2px) scale(1.04);
    border-color: #34D399;
    box-shadow: 0 0 20px 2px rgba(16, 185, 129, 0.5);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0) scale(1);
    border-color: rgba(16, 185, 129, 0.5);
    box-shadow: 0 0 12px -2px rgba(16, 185, 129, 0.25);
  }}
}}

@keyframes capablSkillMissingSeq {{
  0% {{
    opacity: 0;
    transform: translateY(12px) scale(0.9);
    border-color: rgba(239, 68, 68, 0.2);
  }}
  70% {{
    opacity: 1;
    transform: translateY(-2px) scale(1.03);
    border-color: #F87171;
    box-shadow: 0 0 18px 2px rgba(239, 68, 68, 0.4);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0) scale(1);
    border-color: rgba(239, 68, 68, 0.45);
    box-shadow: 0 0 10px -2px rgba(239, 68, 68, 0.2);
  }}
}}

@keyframes capablResultSettle {{
  0% {{
    opacity: 0;
    transform: translateY(20px) scale(0.96);
    filter: blur(4px);
  }}
  70% {{
    opacity: 0.95;
    transform: translateY(-2px) scale(1.005);
    filter: blur(0);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }}
}}

/* 38. SIGNATURE EVIDENCE ANIMATION: 4-Stage Progressive Unfold */
@keyframes capablEvidenceCardExpand {{
  0% {{
    max-height: 80px;
    opacity: 0.85;
    transform: scale(0.99);
  }}
  100% {{
    max-height: 1400px;
    opacity: 1;
    transform: scale(1);
  }}
}}

@keyframes capablEvidenceMetaAppear {{
  0% {{
    opacity: 0;
    transform: translateY(-6px);
  }}
  100% {{
    opacity: 1;
    transform: translateY(0);
  }}
}}

@keyframes capablEvidenceSourceReveal {{
  0% {{
    opacity: 0;
    transform: translateX(-10px);
  }}
  100% {{
    opacity: 1;
    transform: translateX(0);
  }}
}}

@keyframes capablEvidenceContentReadable {{
  0% {{
    opacity: 0;
    filter: blur(3px);
  }}
  100% {{
    opacity: 1;
    filter: blur(0);
  }}
}}

/* 39. SIGNATURE AGENT ANIMATION: 4-State Vertical Progression */
@keyframes capablAgentStateStepActive {{
  0%, 100% {{
    border-color: rgba(6, 182, 212, 0.4);
    box-shadow: 0 0 14px -2px rgba(6, 182, 212, 0.3);
    transform: translateX(0);
  }}
  50% {{
    border-color: #06B6D4;
    box-shadow: 0 0 24px 3px rgba(6, 182, 212, 0.55);
    transform: translateX(4px);
  }}
}}

@keyframes capablAgentRailFlow {{
  0% {{
    background-position: 0 0;
  }}
  100% {{
    background-position: 0 40px;
  }}
}}

/* Stagger Delays (0 to 12) */
.stagger-1 {{ animation-delay: 50ms; }}
.stagger-2 {{ animation-delay: 100ms; }}
.stagger-3 {{ animation-delay: 150ms; }}
.stagger-4 {{ animation-delay: 200ms; }}
.stagger-5 {{ animation-delay: 250ms; }}
.stagger-6 {{ animation-delay: 300ms; }}
.stagger-7 {{ animation-delay: 350ms; }}
.stagger-8 {{ animation-delay: 400ms; }}
.stagger-9 {{ animation-delay: 450ms; }}
.stagger-10 {{ animation-delay: 500ms; }}
.stagger-11 {{ animation-delay: 550ms; }}
.stagger-12 {{ animation-delay: 600ms; }}

/* -----------------------------------------------------------------------------
   3. MICRO-INTERACTION RULES (BUTTONS, CARDS, INPUTS)
   ----------------------------------------------------------------------------- */

/* Button Transitions */
.stButton > button,
button.capabl-btn {{
  transition: 
    background-color var(--capabl-dur-fast) var(--capabl-ease-smooth),
    border-color var(--capabl-dur-fast) var(--capabl-ease-smooth),
    transform var(--capabl-dur-fast) var(--capabl-ease-spring),
    box-shadow var(--capabl-dur-fast) var(--capabl-ease-smooth) !important;
}}

.stButton > button:hover,
button.capabl-btn:hover {{
  transform: translateY(-1.5px) !important;
  box-shadow: 0 4px 16px -2px rgba(99, 102, 241, 0.28) !important;
}}

.stButton > button:active,
button.capabl-btn:active {{
  transform: scale(0.98) translateY(0) !important;
  transition-duration: var(--capabl-dur-instant) !important;
}}

/* Card Interactive Hover Lift & Glow */
.capabl-card-interactive {{
  transition:
    transform var(--capabl-dur-fast) var(--capabl-ease-spring),
    border-color var(--capabl-dur-fast) var(--capabl-ease-smooth),
    box-shadow var(--capabl-dur-fast) var(--capabl-ease-smooth) !important;
}}

.capabl-card-interactive:hover {{
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.16) !important;
  box-shadow: 0 12px 28px -6px rgba(0, 0, 0, 0.65), 0 0 16px -2px rgba(99, 102, 241, 0.12) !important;
}}

/* Status Indicator Dot */
.capabl-status-dot-active {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #10B981;
  display: inline-block;
  animation: capablStatusPulse 2.4s ease-in-out infinite;
}}

.capabl-status-dot-amber {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #F59E0B;
  display: inline-block;
}}

/* Skeleton Loader Utility */
.capabl-skeleton {{
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.03) 0%,
    rgba(255, 255, 255, 0.08) 50%,
    rgba(255, 255, 255, 0.03) 100%
  );
  background-size: 200% 100%;
  animation: capablShimmer 1.8s infinite;
  border-radius: 6px;
}}

/* -----------------------------------------------------------------------------
   4. ACCESSIBILITY: REDUCED MOTION SUPPORT
   ----------------------------------------------------------------------------- */

@media (prefers-reduced-motion: reduce) {{
  *,
  *::before,
  *::after {{
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }}
  .capabl-status-dot-active {{
    animation: none !important;
  }}
  .motion-agent-active {{
    animation: none !important;
  }}
  .capabl-skeleton {{
    animation: none !important;
    background: rgba(255, 255, 255, 0.05) !important;
  }}
}}
"""
