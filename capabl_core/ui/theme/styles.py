"""
Master Styling Engine for CAPABL Recruitment Intelligence OS.

Phase 1: Premium Visual Language & Motion System.
Generates comprehensive enterprise dark theme CSS, glassmorphic surface
rules, typography hierarchy, widget overrides, and theme injection.
"""

from typing import Optional
import streamlit as st

from capabl_core.ui.theme.tokens import (
    COLORS,
    TYPOGRAPHY,
    SPACING,
    RADIUS,
    ELEVATION,
    MOTION,
)
from capabl_core.ui.theme.motion import generate_motion_css


def generate_theme_css() -> str:
    """
    Builds authoritative production CSS combining tokens, motion engine,
    and Streamlit widget overrides.
    """
    motion_css = generate_motion_css()

    return f"""
<style>
/* -----------------------------------------------------------------------------
   GOOGLE FONTS IMPORT
   ----------------------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

{motion_css}

/* -----------------------------------------------------------------------------
   GLOBAL CANVAS & TYPOGRAPHY
   ----------------------------------------------------------------------------- */
html, body, .stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"], section.main {{
  font-family: {TYPOGRAPHY.FONT_FAMILY_SANS} !important;
  background-color: {COLORS.CANVAS_BASE} !important;
  color: {COLORS.TEXT_PRIMARY} !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}

/* Ambient Canvas Glow (Restrained, Calm, Non-Distracting) */
.stApp, [data-testid="stAppViewContainer"], section.main {{
  background: 
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.09), transparent 70%),
    radial-gradient(ellipse 60% 40% at 90% 10%, rgba(6, 182, 212, 0.05), transparent 60%),
    {COLORS.CANVAS_BASE} !important;
  background-attachment: fixed !important;
}}

/* Headings and Content Typography */
h1, h2, h3, h4, h5, h6 {{
  color: {COLORS.TEXT_PRIMARY} !important;
  font-family: {TYPOGRAPHY.FONT_FAMILY_SANS} !important;
  letter-spacing: -0.02em !important;
}}

p, span, label, li {{
  color: {COLORS.TEXT_PRIMARY} !important;
}}

.stMarkdown p {{
  color: {COLORS.TEXT_SECONDARY} !important;
  line-height: 1.6 !important;
}}

/* Alert / Info / Status Card Overrides */
[data-testid="stAlert"] {{
  background-color: {COLORS.SURFACE_GLASS} !important;
  border: 1px solid {COLORS.BORDER_MUTED} !important;
  border-radius: {RADIUS.RADIUS_MD} !important;
  color: {COLORS.TEXT_PRIMARY} !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  box-shadow: {ELEVATION.SHADOW_LOW} !important;
}}

[data-testid="stAlert"] * {{
  color: {COLORS.TEXT_PRIMARY} !important;
}}

/* Streamlit Header Bar Clean Removal */
[data-testid="stHeader"] {{
  background: rgba(8, 11, 17, 0.75) !important;
  backdrop-filter: blur(12px) !important;
  border-bottom: 1px solid {COLORS.BORDER_HAIRLINE} !important;
}}

/* Main Block Padding */
[data-testid="stMainBlockContainer"] {{
  padding-top: 2rem !important;
  padding-bottom: 4rem !important;
  max-width: 1400px !important;
}}

/* -----------------------------------------------------------------------------
   SIDEBAR SURFACES & NAVIGATION
   ----------------------------------------------------------------------------- */
[data-testid="stSidebar"] {{
  background-color: {COLORS.SURFACE_SUBTLE} !important;
  border-right: 1px solid {COLORS.BORDER_MUTED} !important;
}}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
  background: transparent !important;
}}

/* -----------------------------------------------------------------------------
   STREAMLIT WIDGET OVERRIDES: BUTTONS
   ----------------------------------------------------------------------------- */
/* Primary Buttons */
[data-testid="stBaseButton-primary"],
.stButton > button[kind="primary"] {{
  background: linear-gradient(180deg, #6366F1 0%, #4F46E5 100%) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(255, 255, 255, 0.18) !important;
  border-radius: {RADIUS.RADIUS_SM} !important;
  font-weight: 600 !important;
  font-size: {TYPOGRAPHY.SIZE_SM} !important;
  letter-spacing: -0.01em !important;
  padding: 0.55rem 1.15rem !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4), 0 0 12px -2px rgba(99, 102, 241, 0.35) !important;
}}

[data-testid="stBaseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {{
  background: linear-gradient(180deg, #6B70F5 0%, #564DE8 100%) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
  box-shadow: 0 4px 20px -2px rgba(99, 102, 241, 0.5) !important;
}}

/* Secondary / Default Buttons */
[data-testid="stBaseButton-secondary"],
.stButton > button {{
  background-color: {COLORS.SURFACE_RAISED} !important;
  color: {COLORS.TEXT_PRIMARY} !important;
  border: 1px solid {COLORS.BORDER_MUTED} !important;
  border-radius: {RADIUS.RADIUS_SM} !important;
  font-weight: 500 !important;
  font-size: {TYPOGRAPHY.SIZE_SM} !important;
  padding: 0.55rem 1.15rem !important;
  box-shadow: {ELEVATION.SHADOW_LOW} !important;
}}

[data-testid="stBaseButton-secondary"]:hover,
.stButton > button:hover {{
  background-color: rgba(255, 255, 255, 0.06) !important;
  border-color: {COLORS.BORDER_PROMINENT} !important;
  color: #FFFFFF !important;
}}

/* -----------------------------------------------------------------------------
   STREAMLIT WIDGET OVERRIDES: FORM INPUTS
   ----------------------------------------------------------------------------- */
/* Text Input & Textarea */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
  background-color: {COLORS.SURFACE_SUBTLE} !important;
  color: {COLORS.TEXT_PRIMARY} !important;
  border: 1px solid {COLORS.BORDER_MUTED} !important;
  border-radius: {RADIUS.RADIUS_SM} !important;
  font-size: {TYPOGRAPHY.SIZE_SM} !important;
  transition: border-color {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT}, box-shadow {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT} !important;
}}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
  border-color: {COLORS.BORDER_FOCUS} !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}}

/* File Uploader Container */
[data-testid="stFileUploader"] {{
  background-color: {COLORS.SURFACE_GLASS} !important;
  border: 1px dashed {COLORS.BORDER_PROMINENT} !important;
  border-radius: {RADIUS.RADIUS_MD} !important;
  padding: {SPACING.SPACE_SM} !important;
  transition: border-color {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT}, background-color {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT} !important;
}}

[data-testid="stFileUploader"]:hover {{
  border-color: {COLORS.BRAND_PRIMARY} !important;
  background-color: rgba(99, 102, 241, 0.04) !important;
}}

/* Selectbox Dropdown */
[data-testid="stSelectbox"] > div > div {{
  background-color: {COLORS.SURFACE_SUBTLE} !important;
  border: 1px solid {COLORS.BORDER_MUTED} !important;
  border-radius: {RADIUS.RADIUS_SM} !important;
  color: {COLORS.TEXT_PRIMARY} !important;
}}

/* Checkbox Accent */
[data-testid="stCheckbox"] label {{
  font-size: {TYPOGRAPHY.SIZE_SM} !important;
  color: {COLORS.TEXT_PRIMARY} !important;
}}

/* -----------------------------------------------------------------------------
   STREAMLIT WIDGET OVERRIDES: TABS
   ----------------------------------------------------------------------------- */
.stTabs [data-baseweb="tab-list"] {{
  background-color: {COLORS.SURFACE_SUBTLE} !important;
  border-bottom: 1px solid {COLORS.BORDER_MUTED} !important;
  border-radius: {RADIUS.RADIUS_SM} {RADIUS.RADIUS_SM} 0 0 !important;
  padding: 0 {SPACING.SPACE_XS} !important;
  gap: {SPACING.SPACE_XS} !important;
}}

.stTabs [data-baseweb="tab"] {{
  color: {COLORS.TEXT_MUTED} !important;
  font-weight: 500 !important;
  font-size: {TYPOGRAPHY.SIZE_SM} !important;
  border-radius: {RADIUS.RADIUS_XS} {RADIUS.RADIUS_XS} 0 0 !important;
  padding: 0.65rem 1rem !important;
  border-bottom: 2px solid transparent !important;
  transition: color {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT}, border-color {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT} !important;
}}

.stTabs [aria-selected="true"] {{
  color: {COLORS.TEXT_PRIMARY} !important;
  font-weight: 600 !important;
  border-bottom: 2px solid {COLORS.BRAND_PRIMARY} !important;
  background-color: rgba(255, 255, 255, 0.02) !important;
}}

/* -----------------------------------------------------------------------------
   STREAMLIT WIDGET OVERRIDES: METRICS & EXPANDERS
   ----------------------------------------------------------------------------- */
[data-testid="stMetric"] {{
  background-color: {COLORS.SURFACE_GLASS} !important;
  border: 1px solid {COLORS.BORDER_MUTED} !important;
  border-radius: {RADIUS.RADIUS_MD} !important;
  padding: {SPACING.SPACE_MD} {SPACING.SPACE_LG} !important;
  box-shadow: {ELEVATION.SHADOW_LOW} !important;
}}

[data-testid="stMetricLabel"] {{
  color: {COLORS.TEXT_MUTED} !important;
  font-size: {TYPOGRAPHY.SIZE_XS} !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}}

[data-testid="stMetricValue"] {{
  color: {COLORS.TEXT_PRIMARY} !important;
  font-weight: 700 !important;
  font-size: {TYPOGRAPHY.SIZE_2XL} !important;
  letter-spacing: -0.02em !important;
}}

/* Expanders */
.streamlit-expanderHeader {{
  background-color: {COLORS.SURFACE_RAISED} !important;
  border: 1px solid {COLORS.BORDER_MUTED} !important;
  border-radius: {RADIUS.RADIUS_SM} !important;
  color: {COLORS.TEXT_PRIMARY} !important;
  font-size: {TYPOGRAPHY.SIZE_SM} !important;
  font-weight: 500 !important;
}}

/* -----------------------------------------------------------------------------
   CUSTOM REUSABLE ENTERPRISE UI SURFACES
   ----------------------------------------------------------------------------- */
.capabl-glass-card {{
  background: {COLORS.SURFACE_GLASS};
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid {COLORS.BORDER_MUTED};
  border-radius: {RADIUS.RADIUS_MD};
  padding: {SPACING.SPACE_LG};
  box-shadow: {ELEVATION.SHADOW_MEDIUM};
}}

.capabl-glass-card-elevated {{
  background: {COLORS.SURFACE_OVERLAY};
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid {COLORS.BORDER_PROMINENT};
  border-radius: {RADIUS.RADIUS_LG};
  padding: {SPACING.SPACE_XL};
  box-shadow: {ELEVATION.SHADOW_HIGH};
}}

/* Metric Summary Card */
.capabl-kpi-card {{
  background: {COLORS.SURFACE_GLASS};
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid {COLORS.BORDER_MUTED};
  border-radius: {RADIUS.RADIUS_MD};
  padding: 1.15rem 1.25rem;
  box-shadow: {ELEVATION.SHADOW_LOW};
  transition: transform {MOTION.DURATION_FAST} {MOTION.EASE_SPRING}, border-color {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT}, box-shadow {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT};
}}

.capabl-kpi-card:hover {{
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.45) !important;
  box-shadow: 0 16px 36px -6px rgba(0, 0, 0, 0.75), 0 0 20px -2px rgba(99, 102, 241, 0.25) !important;
}}

.capabl-kpi-label {{
  font-size: {TYPOGRAPHY.SIZE_XS};
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: {COLORS.TEXT_MUTED};
  font-weight: 600;
  margin-bottom: 0.25rem;
}}

.capabl-kpi-val {{
  font-size: 1.85rem;
  font-weight: 700;
  color: {COLORS.TEXT_PRIMARY};
  letter-spacing: -0.02em;
}}

.capabl-count-val {{
  display: inline-block;
  animation: capablCountPop 0.65s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}}

/* Semantic Chips (Skills, Statuses) */
.capabl-chip {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: {RADIUS.RADIUS_SM};
  font-size: {TYPOGRAPHY.SIZE_XS};
  font-weight: 600;
  letter-spacing: -0.01em;
  margin-right: 0.35rem;
  margin-bottom: 0.35rem;
}}

.capabl-chip-match {{
  background-color: {COLORS.SUCCESS_SURFACE};
  color: {COLORS.SUCCESS_LIGHT};
  border: 1px solid {COLORS.SUCCESS_BORDER};
}}

.capabl-chip-gap {{
  background-color: {COLORS.DANGER_SURFACE};
  color: {COLORS.DANGER_LIGHT};
  border: 1px solid {COLORS.DANGER_BORDER};
}}

.capabl-chip-neutral {{
  background-color: rgba(255, 255, 255, 0.04);
  color: {COLORS.TEXT_SECONDARY};
  border: 1px solid {COLORS.BORDER_MUTED};
}}

.capabl-chip-brand {{
  background-color: {COLORS.BRAND_SURFACE};
  color: #A5B4FC;
  border: 1px solid {COLORS.BRAND_BORDER};
}}

/* Clean Custom Scrollbars */
::-webkit-scrollbar {{
  width: 6px;
  height: 6px;
}}
::-webkit-scrollbar-track {{
  background: {COLORS.CANVAS_BASE};
}}
::-webkit-scrollbar-thumb {{
  background: rgba(255, 255, 255, 0.12);
  border-radius: 9999px;
}}
::-webkit-scrollbar-thumb:hover {{
  background: rgba(255, 255, 255, 0.22);
}}

/* -----------------------------------------------------------------------------
   PHASE 3: ACTIVITY TIMELINE & INTELLIGENCE PANEL STYLES
   ----------------------------------------------------------------------------- */
.capabl-timeline {{
  position: relative;
  padding-left: 1.5rem;
  margin-top: 0.75rem;
}}

.capabl-timeline::before {{
  content: "";
  position: absolute;
  left: 7px;
  top: 6px;
  bottom: 6px;
  width: 2px;
  background: rgba(255, 255, 255, 0.08);
}}

.capabl-timeline-item {{
  position: relative;
  margin-bottom: 1.15rem;
  animation: capablCardEnter {MOTION.DURATION_STANDARD} {MOTION.EASE_SPRING} both;
}}

.capabl-timeline-dot {{
  position: absolute;
  left: -1.5rem;
  top: 4px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #121824;
  border: 2px solid {COLORS.BRAND_PRIMARY};
  box-shadow: 0 0 10px rgba(99, 102, 241, 0.4);
}}

.capabl-timeline-content {{
  background: rgba(18, 24, 38, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: {RADIUS.RADIUS_SM};
  padding: 0.65rem 0.95rem;
  transition: all {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT};
}}

.capabl-timeline-content:hover {{
  background: rgba(255, 255, 255, 0.04);
  border-color: {COLORS.BRAND_BORDER};
  transform: translateX(4px);
}}

.capabl-panel-card {{
  background: {COLORS.SURFACE_GLASS};
  backdrop-filter: blur(14px);
  border: 1px solid {COLORS.BORDER_MUTED};
  border-radius: {RADIUS.RADIUS_MD};
  padding: 1.15rem;
  box-shadow: {ELEVATION.SHADOW_LOW};
  transition: all {MOTION.DURATION_FAST} {MOTION.EASE_SPRING};
}}

.capabl-panel-card:hover {{
  border-color: {COLORS.BORDER_FOCUS};
  box-shadow: {ELEVATION.SHADOW_MEDIUM}, 0 0 16px -2px rgba(99, 102, 241, 0.15);
  transform: translateY(-2px);
}}

.capabl-system-state-bar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 1.15rem;
  background: {COLORS.SURFACE_GLASS};
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid {COLORS.BORDER_MUTED};
  border-radius: {RADIUS.RADIUS_SM};
  margin-top: 0.5rem;
  margin-bottom: 1.25rem;
  box-shadow: {ELEVATION.SHADOW_LOW};
}}

/* -----------------------------------------------------------------------------
   PHASE 4: CANDIDATE WORKSPACE & DOCUMENT PROCESSING STYLES
   ----------------------------------------------------------------------------- */
.capabl-candidate-card {{
  background: {COLORS.SURFACE_GLASS};
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid {COLORS.BORDER_MUTED};
  border-radius: {RADIUS.RADIUS_MD};
  padding: 1.25rem;
  box-shadow: {ELEVATION.SHADOW_LOW};
  transition: all {MOTION.DURATION_FAST} {MOTION.EASE_SPRING};
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}

.capabl-candidate-card:hover {{
  transform: translateY(-3px);
  border-color: rgba(99, 102, 241, 0.45) !important;
  box-shadow: 0 16px 36px -6px rgba(0, 0, 0, 0.75), 0 0 20px -2px rgba(99, 102, 241, 0.25) !important;
}}

.capabl-candidate-card-selected {{
  border-color: {COLORS.BRAND_PRIMARY} !important;
  background: rgba(99, 102, 241, 0.08) !important;
  box-shadow: 0 0 24px -2px rgba(99, 102, 241, 0.35) !important;
}}

.capabl-step-card {{
  background: rgba(18, 24, 38, 0.6);
  border: 1px solid {COLORS.BORDER_MUTED};
  border-radius: {RADIUS.RADIUS_SM};
  padding: 0.85rem 1.15rem;
  margin-bottom: 0.65rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT};
}}

.capabl-step-card-active {{
  border-color: {COLORS.CYAN_PRIMARY};
  background: rgba(6, 182, 212, 0.08);
  box-shadow: 0 0 16px -2px rgba(6, 182, 212, 0.25);
}}

.capabl-step-card-complete {{
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.05);
}}

.capabl-scanner-box {{
  position: relative;
  overflow: hidden;
  border: 1px dashed {COLORS.BRAND_BORDER};
  border-radius: {RADIUS.RADIUS_MD};
  padding: 1.5rem;
  background: rgba(99, 102, 241, 0.03);
}}

.capabl-scanner-beam {{
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #06B6D4, #6366F1, transparent);
  box-shadow: 0 0 12px #06B6D4;
  animation: capablScanLine 2s ease-in-out infinite;
}}

.capabl-table {{
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin-top: 0.75rem;
  border-radius: {RADIUS.RADIUS_MD};
  overflow: hidden;
  border: 1px solid {COLORS.BORDER_MUTED};
}}

.capabl-table th {{
  background: {COLORS.SURFACE_RAISED};
  color: {COLORS.TEXT_MUTED};
  font-size: {TYPOGRAPHY.SIZE_XS};
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid {COLORS.BORDER_MUTED};
  text-align: left;
}}

.capabl-table td {{
  background: {COLORS.SURFACE_GLASS};
  color: {COLORS.TEXT_PRIMARY};
  font-size: {TYPOGRAPHY.SIZE_SM};
  padding: 0.85rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}}

.capabl-table-row:hover td {{
  background: rgba(255, 255, 255, 0.04);
}}

/* -----------------------------------------------------------------------------
   PHASE 5: JOB REQUISITION WORKSPACE STYLES
   ----------------------------------------------------------------------------- */
.capabl-job-card {{
  background: {COLORS.SURFACE_GLASS};
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid {COLORS.BORDER_MUTED};
  border-radius: {RADIUS.RADIUS_MD};
  padding: 1.25rem;
  box-shadow: {ELEVATION.SHADOW_LOW};
  transition: all {MOTION.DURATION_FAST} {MOTION.EASE_SPRING};
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}

.capabl-job-card:hover {{
  transform: translateY(-3px);
  border-color: rgba(6, 182, 212, 0.45) !important;
  box-shadow: 0 16px 36px -6px rgba(0, 0, 0, 0.75), 0 0 20px -2px rgba(6, 182, 212, 0.25) !important;
}}

.capabl-job-card-selected {{
  border-color: {COLORS.CYAN_PRIMARY} !important;
  background: rgba(6, 182, 212, 0.08) !important;
  box-shadow: 0 0 24px -2px rgba(6, 182, 212, 0.35) !important;
}}

.capabl-chip-active {{
  background: rgba(16, 185, 129, 0.12) !important;
  border: 1px solid rgba(16, 185, 129, 0.4) !important;
  color: #34D399 !important;
}}

.capabl-chip-closed {{
  background: rgba(239, 68, 68, 0.12) !important;
  border: 1px solid rgba(239, 68, 68, 0.4) !important;
  color: #F87171 !important;
}}

.capabl-chip-dept {{
  background: rgba(99, 102, 241, 0.12) !important;
  border: 1px solid rgba(99, 102, 241, 0.35) !important;
  color: #A5B4FC !important;
}}

.capabl-chip-loc {{
  background: rgba(6, 182, 212, 0.12) !important;
  border: 1px solid rgba(6, 182, 212, 0.35) !important;
  color: #67E8F9 !important;
}}

.capabl-chip-stagger {{
  display: inline-flex;
  align-items: center;
  margin-right: 0.4rem;
  margin-bottom: 0.45rem;
  animation: capablChipFadeIn 0.38s var(--capabl-ease-spring) both;
}}

/* -----------------------------------------------------------------------------
   PHASE 6: MATCH INTELLIGENCE & CINEMATIC COMPARISON STYLES
   ----------------------------------------------------------------------------- */
.capabl-pipeline-container {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  position: relative;
  overflow: hidden;
}}

.capabl-pipeline-step {{
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  flex: 1;
  padding: 0.65rem 0.85rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  z-index: 2;
}}

.capabl-pipeline-step-active {{
  background: rgba(6, 182, 212, 0.12) !important;
  border-color: #06B6D4 !important;
  box-shadow: 0 0 20px -2px rgba(6, 182, 212, 0.45);
  animation: capablPipelinePulse 2.4s ease-in-out infinite;
}}

.capabl-pipeline-step-complete {{
  background: rgba(16, 185, 129, 0.08) !important;
  border-color: rgba(16, 185, 129, 0.4) !important;
}}

.capabl-pipeline-arrow {{
  color: #64748B;
  font-size: 1.2rem;
  font-weight: 700;
  padding: 0 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}}

.capabl-chip-reveal-match {{
  display: inline-flex;
  align-items: center;
  padding: 0.45rem 0.9rem !important;
  border-radius: 8px !important;
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  background: rgba(16, 185, 129, 0.12) !important;
  border: 1px solid rgba(16, 185, 129, 0.45) !important;
  color: #34D399 !important;
  box-shadow: 0 0 16px -2px rgba(16, 185, 129, 0.35) !important;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  margin-right: 0.5rem;
  margin-bottom: 0.6rem;
  animation: capablSkillSequentialReveal 0.42s cubic-bezier(0.16, 1, 0.3, 1) both;
}}

.capabl-chip-reveal-match:hover {{
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 0 24px 2px rgba(16, 185, 129, 0.5) !important;
  border-color: #34D399 !important;
}}

.capabl-chip-reveal-missing {{
  display: inline-flex;
  align-items: center;
  padding: 0.45rem 0.9rem !important;
  border-radius: 8px !important;
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  background: rgba(239, 68, 68, 0.10) !important;
  border: 1px solid rgba(239, 68, 68, 0.45) !important;
  color: #F87171 !important;
  box-shadow: 0 0 16px -2px rgba(239, 68, 68, 0.22) !important;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  margin-right: 0.5rem;
  margin-bottom: 0.6rem;
  animation: capablSkillSequentialReveal 0.42s cubic-bezier(0.16, 1, 0.3, 1) both;
}}

.capabl-chip-reveal-missing:hover {{
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 0 24px 2px rgba(239, 68, 68, 0.4) !important;
  border-color: #F87171 !important;
}}

.capabl-evidence-drawer {{
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid #06B6D4;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 16px 36px -4px rgba(0, 0, 0, 0.8), 0 0 28px -2px rgba(6, 182, 212, 0.25);
  animation: capablDrawerSlide 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  margin-top: 1rem;
  margin-bottom: 1.5rem;
}}

.capabl-evidence-drawer-missing {{
  background: rgba(26, 16, 24, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 16px 36px -4px rgba(0, 0, 0, 0.8), 0 0 28px -2px rgba(239, 68, 68, 0.2);
  animation: capablDrawerSlide 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  margin-top: 1rem;
  margin-bottom: 1.5rem;
}}

/* =============================================================================
   SIGNATURE MATCH ANIMATION CLASSES
   ============================================================================= */
.capabl-signature-match-container {{
  background: rgba(10, 14, 26, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(99, 102, 241, 0.22);
  border-radius: 14px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.6);
}}

.capabl-match-processing-panel {{
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(6, 182, 212, 0.45);
  border-radius: 10px;
  padding: 0.9rem 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
  animation: capablMatchProcessPulse 2.5s ease-in-out infinite;
}}

.capabl-requirements-resolve-card {{
  background: rgba(18, 24, 40, 0.8);
  border: 1px solid rgba(99, 102, 241, 0.35);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
  animation: capablRequirementsResolve 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}}

.capabl-skill-matched-seq {{
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.48rem 0.95rem;
  border-radius: 8px;
  font-size: 0.86rem;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.5);
  color: #34D399;
  box-shadow: 0 0 14px -2px rgba(16, 185, 129, 0.3);
  animation: capablSkillMatchedSeq 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}}

.capabl-skill-matched-seq:hover {{
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 0 22px 2px rgba(16, 185, 129, 0.55);
  border-color: #34D399;
}}

.capabl-skill-missing-seq {{
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.48rem 0.95rem;
  border-radius: 8px;
  font-size: 0.86rem;
  font-weight: 600;
  background: rgba(239, 68, 68, 0.10);
  border: 1px solid rgba(239, 68, 68, 0.45);
  color: #F87171;
  box-shadow: 0 0 12px -2px rgba(239, 68, 68, 0.25);
  animation: capablSkillMissingSeq 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}}

.capabl-skill-missing-seq:hover {{
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 0 20px 2px rgba(239, 68, 68, 0.45);
  border-color: #F87171;
}}

.capabl-result-settle-card {{
  background: linear-gradient(135deg, rgba(16, 24, 40, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
  border: 1px solid rgba(16, 185, 129, 0.4);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  box-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.7), 0 0 24px -2px rgba(16, 185, 129, 0.2);
  animation: capablResultSettle 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
  margin-top: 1.25rem;
}}

/* =============================================================================
   SIGNATURE EVIDENCE ANIMATION CLASSES
   ============================================================================= */
.capabl-evidence-card-expanding {{
  animation: capablEvidenceCardExpand 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.capabl-ev-meta-reveal {{
  animation: capablEvidenceMetaAppear 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
}}

.capabl-ev-source-reveal {{
  animation: capablEvidenceSourceReveal 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
  animation-delay: 80ms;
}}

.capabl-ev-content-readable {{
  animation: capablEvidenceContentReadable 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
  animation-delay: 140ms;
}}

/* =============================================================================
   SIGNATURE AGENT REASONING RAIL (4-STATE VERTICAL)
   ============================================================================= */
.capabl-agent-vertical-rail {{
  background: rgba(10, 14, 26, 0.88);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
  position: relative;
}}

.capabl-agent-step-vertical {{
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  position: relative;
  padding-bottom: 1.25rem;
}}

.capabl-agent-step-vertical:last-child {{
  padding-bottom: 0;
}}

.capabl-agent-step-vertical:not(:last-child)::after {{
  content: "";
  position: absolute;
  left: 14px;
  top: 30px;
  bottom: 0;
  width: 2px;
  background: rgba(255, 255, 255, 0.1);
}}

.capabl-agent-step-vertical-active:not(:last-child)::after {{
  background: linear-gradient(180deg, #06B6D4 0%, rgba(99, 102, 241, 0.4) 100%) !important;
}}

.capabl-agent-step-vertical-done:not(:last-child)::after {{
  background: #10B981 !important;
}}

.capabl-agent-icon-badge {{
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  z-index: 2;
  flex-shrink: 0;
  background: rgba(15, 23, 42, 0.95);
  border: 2px solid #64748B;
  color: #94A3B8;
  transition: all 0.25s ease;
}}

.capabl-agent-icon-badge-active {{
  border-color: #06B6D4 !important;
  color: #38BDF8 !important;
  box-shadow: 0 0 16px 2px rgba(6, 182, 212, 0.5) !important;
  animation: capablAgentStateStepActive 2.4s ease-in-out infinite;
}}

.capabl-agent-icon-badge-done {{
  border-color: #10B981 !important;
  color: #34D399 !important;
  background: rgba(16, 185, 129, 0.18) !important;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.3) !important;
}}

/* -----------------------------------------------------------------------------
   PHASE 7: EVIDENCE INTELLIGENCE & GRAPH VISUALIZATION
   ----------------------------------------------------------------------------- */
.capabl-evidence-card {{
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.25rem 1.4rem;
  margin-bottom: 1rem;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
  position: relative;
  overflow: hidden;
}}

.capabl-evidence-card:hover {{
  border-color: rgba(6, 182, 212, 0.45);
  transform: translateY(-2px);
  box-shadow: 0 10px 28px -4px rgba(0, 0, 0, 0.7), 0 0 20px -2px rgba(6, 182, 212, 0.18);
}}

.capabl-evidence-card-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.85rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}}

.capabl-evidence-meta-drawer {{
  background: rgba(8, 12, 22, 0.95);
  border: 1px solid rgba(6, 182, 212, 0.35);
  border-radius: 10px;
  padding: 1.1rem 1.25rem;
  margin-top: 1rem;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.6), 0 0 20px -4px rgba(6, 182, 212, 0.2);
  animation: capablCardExpand 0.32s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.capabl-highlight {{
  background-color: rgba(245, 158, 11, 0.25);
  border-bottom: 1.5px solid #F59E0B;
  color: #FDE68A;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-weight: 600;
  display: inline;
  animation: capablHighlightPulse 3s ease-in-out infinite;
}}

.capabl-evidence-graph-container {{
  background: rgba(10, 14, 26, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 14px;
  padding: 1.5rem;
  margin-bottom: 1.75rem;
  box-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.65), 0 0 24px -2px rgba(99, 102, 241, 0.15);
}}

.capabl-graph-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: nowrap;
}}

.capabl-graph-node {{
  flex: 1;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  min-width: 180px;
  position: relative;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}}

.capabl-graph-node-req {{
  border-color: rgba(6, 182, 212, 0.45);
  box-shadow: 0 0 16px -2px rgba(6, 182, 212, 0.25);
}}

.capabl-graph-node-ev {{
  border-color: rgba(16, 185, 129, 0.45);
  box-shadow: 0 0 16px -2px rgba(16, 185, 129, 0.25);
}}

.capabl-graph-node-src {{
  border-color: rgba(99, 102, 241, 0.45);
  box-shadow: 0 0 16px -2px rgba(99, 102, 241, 0.25);
}}

.capabl-graph-connector {{
  width: 60px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}}

.capabl-loading-sequence {{
  display: flex;
  align-items: center;
  justify-content: space-around;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 10px;
  padding: 0.85rem 1.25rem;
  margin-bottom: 1.25rem;
  animation: capablCardEnter 0.3s ease-out forwards;
}}

.capabl-loading-step {{
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: #94A3B8;
}}

.capabl-loading-step-active {{
  color: #38BDF8 !important;
  animation: capablLoadingPulse 1.5s ease-in-out infinite;
}}

.capabl-loading-step-complete {{
  color: #34D399 !important;
}}

.capabl-domain-badge {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: 6px;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}}

.capabl-domain-candidate {{
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.4);
  color: #34D399;
}}

.capabl-domain-job {{
  background: rgba(6, 182, 212, 0.12);
  border: 1px solid rgba(6, 182, 212, 0.4);
  color: #38BDF8;
}}

.capabl-domain-policy {{
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.4);
  color: #FBBF24;
}}

/* -----------------------------------------------------------------------------
   PHASE 8: AGENT INTELLIGENCE WORKSPACE (CONTEXT, ACTIVITY RAIL, CHAT, COMPOSER)
   ----------------------------------------------------------------------------- */
.capabl-agent-context-banner {{
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(99, 102, 241, 0.35);
  border-radius: 12px;
  padding: 0.85rem 1.25rem;
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5), 0 0 16px -2px rgba(99, 102, 241, 0.15);
}}

.capabl-activity-rail {{
  background: rgba(10, 14, 26, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(6, 182, 212, 0.25);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 8px 24px -2px rgba(0, 0, 0, 0.6);
  position: relative;
}}

.capabl-activity-step {{
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  position: relative;
  padding-bottom: 1rem;
}}

.capabl-activity-step:last-child {{
  padding-bottom: 0;
}}

.capabl-activity-step:not(:last-child)::after {{
  content: "";
  position: absolute;
  left: 11px;
  top: 24px;
  bottom: 0;
  width: 2px;
  background: linear-gradient(180deg, rgba(6, 182, 212, 0.6) 0%, rgba(99, 102, 241, 0.3) 100%);
  animation: capablActivityLinePulse 2s ease-in-out infinite;
}}

.capabl-activity-step-done:not(:last-child)::after {{
  background: #10B981 !important;
}}

.capabl-activity-dot {{
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  z-index: 2;
  flex-shrink: 0;
  background: rgba(15, 23, 42, 0.9);
  border: 2px solid #64748B;
  color: #94A3B8;
}}

.capabl-activity-dot-active {{
  border-color: #06B6D4 !important;
  color: #38BDF8 !important;
  box-shadow: 0 0 12px rgba(6, 182, 212, 0.6);
  animation: capablStatusPulse 1.8s infinite;
}}

.capabl-activity-dot-done {{
  border-color: #10B981 !important;
  color: #34D399 !important;
  background: rgba(16, 185, 129, 0.15) !important;
}}

.capabl-chat-msg-user {{
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.25) 0%, rgba(99, 102, 241, 0.15) 100%);
  border: 1px solid rgba(99, 102, 241, 0.4);
  border-radius: 14px 14px 2px 14px;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
  color: #F8FAFC;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  animation: capablMessageSlideIn 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.capabl-chat-msg-agent {{
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 14px 14px 14px 2px;
  padding: 1.15rem 1.35rem;
  margin-bottom: 1.25rem;
  color: #E2E8F0;
  box-shadow: 0 8px 24px -2px rgba(0, 0, 0, 0.6), 0 0 18px -2px rgba(6, 182, 212, 0.15);
  animation: capablMessageSlideIn 0.32s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.capabl-citation-pill {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  font-family: monospace;
  background: rgba(6, 182, 212, 0.12);
  border: 1px solid rgba(6, 182, 212, 0.35);
  color: #38BDF8;
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 0.2rem 0.25rem;
}}

.capabl-citation-pill:hover {{
  background: rgba(6, 182, 212, 0.25);
  border-color: #38BDF8;
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.35);
  transform: translateY(-1px);
}}

.capabl-slash-pill {{
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.3rem 0.65rem;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94A3B8;
  cursor: pointer;
  transition: all 0.2s ease;
}}

.capabl-slash-pill:hover {{
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.4);
  color: #A5B4FC;
}}

.capabl-context-action-card {{
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 0.9rem 1.1rem;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  margin-bottom: 0.75rem;
}}

.capabl-context-action-card:hover {{
  border-color: rgba(6, 182, 212, 0.5);
  background: rgba(6, 182, 212, 0.08);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px -2px rgba(6, 182, 212, 0.2);
}}

/* -----------------------------------------------------------------------------
   PHASE 9: INTERVIEW OPERATIONS (CALENDAR, CARDS, BOOKING FLOW, CELEBRATION)
   ----------------------------------------------------------------------------- */
.capabl-interview-card {{
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.15rem 1.35rem;
  margin-bottom: 0.85rem;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 18px -2px rgba(0, 0, 0, 0.5);
  position: relative;
}}

.capabl-interview-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 10px 24px -2px rgba(0, 0, 0, 0.7);
}}

.capabl-interview-card-booked {{
  border-color: rgba(16, 185, 129, 0.45) !important;
  background: rgba(16, 185, 129, 0.05) !important;
  box-shadow: 0 4px 20px -2px rgba(16, 185, 129, 0.15) !important;
}}

.capabl-interview-card-booked:hover {{
  border-color: #10B981 !important;
  box-shadow: 0 0 24px -2px rgba(16, 185, 129, 0.35) !important;
}}

.capabl-interview-card-available {{
  border-color: rgba(6, 182, 212, 0.4) !important;
}}

.capabl-interview-card-available:hover {{
  border-color: #06B6D4 !important;
  box-shadow: 0 0 24px -2px rgba(6, 182, 212, 0.3) !important;
}}

.capabl-calendar-container {{
  background: rgba(10, 14, 26, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}}

.capabl-booking-flow-container {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 10px;
  padding: 0.85rem 1.25rem;
  margin-bottom: 1.35rem;
  box-shadow: 0 6px 20px -2px rgba(0, 0, 0, 0.5);
  flex-wrap: wrap;
  gap: 0.5rem;
}}

.capabl-booking-step {{
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: #94A3B8;
}}

.capabl-booking-step-active {{
  color: #38BDF8 !important;
  animation: capablBookingStagePulse 2s infinite;
}}

.capabl-booking-step-done {{
  color: #34D399 !important;
}}

.capabl-success-banner {{
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.12) 100%);
  border: 1px solid #10B981;
  border-radius: 14px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 16px 36px -4px rgba(0, 0, 0, 0.7), 0 0 32px 4px rgba(16, 185, 129, 0.25);
  animation: capablCalendarCheck 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.capabl-stale-slot {{
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
  color: #F87171;
  animation: capablSlotFadeOut 2.5s forwards;
}}

/* -----------------------------------------------------------------------------
   PHASE 10: POLICY INTELLIGENCE WORKSPACE STYLES
   ----------------------------------------------------------------------------- */
.capabl-policy-card {{
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1rem;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 16px -2px rgba(0, 0, 0, 0.4);
  animation: capablPolicyCardEnter 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.capabl-policy-card:hover {{
  border-color: rgba(6, 182, 212, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 10px 28px -4px rgba(0, 0, 0, 0.6), 0 0 16px 1px rgba(6, 182, 212, 0.15);
}}

.capabl-policy-card-selected {{
  border-color: #06B6D4 !important;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(6, 182, 212, 0.08) 100%) !important;
  box-shadow: 0 10px 30px -4px rgba(0, 0, 0, 0.6), 0 0 20px 2px rgba(6, 182, 212, 0.25) !important;
}}

.capabl-policy-detail-header {{
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.4rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 8px 24px -2px rgba(0, 0, 0, 0.5);
}}

.capabl-policy-section-box {{
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  padding: 1.15rem 1.35rem;
  margin-bottom: 0.9rem;
  transition: all 0.25s ease-out;
  animation: capablSectionExpand 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.capabl-policy-section-box:hover {{
  border-color: rgba(56, 189, 248, 0.35);
  background: rgba(15, 23, 42, 0.8);
  box-shadow: 0 6px 18px -2px rgba(0, 0, 0, 0.4);
}}

.capabl-policy-evidence-card {{
  background: rgba(15, 23, 42, 0.8);
  border-left: 3px solid #06B6D4;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0 10px 10px 0;
  padding: 1.1rem 1.25rem;
  margin-bottom: 0.85rem;
  transition: all 0.2s ease;
}}

.capabl-policy-evidence-card:hover {{
  border-left-color: #38BDF8;
  background: rgba(15, 23, 42, 0.95);
  box-shadow: 0 6px 20px -2px rgba(0, 0, 0, 0.5), 0 0 12px rgba(6, 182, 212, 0.15);
}}

.capabl-policy-citation {{
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(6, 182, 212, 0.12);
  color: #38BDF8;
  border: 1px solid rgba(6, 182, 212, 0.4);
  padding: 0.25rem 0.65rem;
  border-radius: 6px;
  font-size: 0.76rem;
  font-family: monospace;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  animation: capablCitationReveal 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.capabl-policy-citation:hover {{
  background: rgba(6, 182, 212, 0.25);
  border-color: #38BDF8;
  box-shadow: 0 0 12px rgba(6, 182, 212, 0.4);
}}

.capabl-policy-qa-container {{
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 12px;
  padding: 1.25rem;
  margin-top: 1.25rem;
  box-shadow: 0 8px 24px -2px rgba(0, 0, 0, 0.5);
}}

.capabl-policy-answer-box {{
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(6, 182, 212, 0.06) 100%);
  border: 1px solid rgba(6, 182, 212, 0.45);
  border-radius: 10px;
  padding: 1.25rem;
  margin-top: 1rem;
  animation: capablMessageSlideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.capabl-domain-badge-isolated {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(16, 185, 129, 0.12);
  color: #34D399;
  border: 1px solid rgba(16, 185, 129, 0.4);
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}

/* -----------------------------------------------------------------------------
   PHASE 2: PRODUCTION APPLICATION SHELL (TOPBAR, SIDEBAR, COMMAND PALETTE)
   ----------------------------------------------------------------------------- */
.capabl-topbar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1.35rem;
  background: {COLORS.SURFACE_GLASS};
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid {COLORS.BORDER_MUTED};
  border-radius: {RADIUS.RADIUS_MD};
  margin-bottom: 1.5rem;
  box-shadow: {ELEVATION.SHADOW_LOW};
  animation: capablPageEnter {MOTION.DURATION_COMPLEX} {MOTION.EASE_SPRING} forwards;
}}

.capabl-topbar-left {{
  display: flex;
  align-items: center;
  gap: 0.85rem;
}}

.capabl-brand-icon {{
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, {COLORS.BRAND_PRIMARY} 0%, {COLORS.CYAN_PRIMARY} 100%);
  border-radius: {RADIUS.RADIUS_SM};
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.1rem;
  color: #FFFFFF;
  box-shadow: 0 0 16px -2px rgba(99, 102, 241, 0.4);
}}

.capabl-brand-title {{
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: {COLORS.TEXT_PRIMARY};
}}

.capabl-brand-badge {{
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  background: {COLORS.BRAND_SURFACE};
  color: #A5B4FC;
  border: 1px solid {COLORS.BRAND_BORDER};
  padding: 2px 8px;
  border-radius: {RADIUS.RADIUS_FULL};
}}

.capabl-topbar-center {{
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  max-width: 480px;
  margin: 0 1rem;
}}

.capabl-search-trigger {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background: {COLORS.SURFACE_RAISED};
  border: 1px solid {COLORS.BORDER_MUTED};
  border-radius: {RADIUS.RADIUS_SM};
  padding: 0.45rem 0.95rem;
  color: {COLORS.TEXT_MUTED};
  font-size: {TYPOGRAPHY.SIZE_SM};
  cursor: pointer;
  transition: all {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT};
}}

.capabl-search-trigger:hover {{
  background: rgba(255, 255, 255, 0.05);
  border-color: {COLORS.BORDER_FOCUS};
  color: {COLORS.TEXT_PRIMARY};
  box-shadow: 0 0 14px -2px rgba(99, 102, 241, 0.25);
}}

.capabl-kbd {{
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 4px;
  padding: 1px 6px;
  font-size: {TYPOGRAPHY.SIZE_2XS};
  font-family: {TYPOGRAPHY.FONT_FAMILY_MONO};
  color: {COLORS.TEXT_SECONDARY};
}}

.capabl-topbar-right {{
  display: flex;
  align-items: center;
  gap: 0.85rem;
}}

.capabl-status-pill {{
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: {COLORS.SUCCESS_SURFACE};
  border: 1px solid {COLORS.SUCCESS_BORDER};
  border-radius: {RADIUS.RADIUS_FULL};
  padding: 0.3rem 0.75rem;
  font-size: {TYPOGRAPHY.SIZE_XS};
  font-weight: 600;
  color: {COLORS.SUCCESS_LIGHT};
}}

.capabl-user-pill {{
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.25rem 0.65rem;
  border-radius: {RADIUS.RADIUS_SM};
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid {COLORS.BORDER_HAIRLINE};
}}

.capabl-avatar {{
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #FFFFFF;
}}

/* -----------------------------------------------------------------------------
   SIDEBAR NAVIGATION ITEMS & ANIMATED TRAVEL INDICATOR
   ----------------------------------------------------------------------------- */
.capabl-nav-section-title {{
  font-size: {TYPOGRAPHY.SIZE_2XS};
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: {COLORS.TEXT_MUTED};
  padding: 0.5rem 0.75rem 0.25rem 0.75rem;
  margin-top: 0.65rem;
}}

.stButton > button.capabl-nav-btn {{
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  text-align: left;
  width: 100%;
  padding: 0.6rem 0.85rem !important;
  border-radius: {RADIUS.RADIUS_SM} !important;
  font-size: {TYPOGRAPHY.SIZE_SM} !important;
  font-weight: 500 !important;
  color: {COLORS.TEXT_SECONDARY} !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  transition: all {MOTION.DURATION_FAST} {MOTION.EASE_SPRING} !important;
}}

.stButton > button.capabl-nav-btn:hover {{
  color: {COLORS.TEXT_PRIMARY} !important;
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: {COLORS.BORDER_HAIRLINE} !important;
  transform: translateX(3px) !important;
}}

.stButton > button.capabl-nav-btn-active {{
  color: #FFFFFF !important;
  background: {COLORS.BRAND_SURFACE} !important;
  border: 1px solid {COLORS.BRAND_BORDER} !important;
  box-shadow: 0 0 16px -2px rgba(99, 102, 241, 0.25) !important;
  font-weight: 600 !important;
  transform: translateX(4px) !important;
}}

.stButton > button.capabl-nav-btn-active::before {{
  content: "";
  position: absolute;
  left: -6px;
  top: 15%;
  height: 70%;
  width: 3px;
  border-radius: 4px;
  background: {COLORS.BRAND_PRIMARY};
  box-shadow: 0 0 8px {COLORS.BRAND_PRIMARY};
  transition: all {MOTION.DURATION_STANDARD} {MOTION.EASE_SPRING};
}}

/* -----------------------------------------------------------------------------
   COMMAND PALETTE MODAL
   ----------------------------------------------------------------------------- */
.capabl-cmd-card {{
  background: {COLORS.SURFACE_OVERLAY};
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid {COLORS.BORDER_FOCUS};
  border-radius: {RADIUS.RADIUS_LG};
  padding: {SPACING.SPACE_LG};
  box-shadow: {ELEVATION.SHADOW_HIGH}, 0 0 32px -4px rgba(99, 102, 241, 0.25);
  animation: capablModalEnter {MOTION.DURATION_STANDARD} {MOTION.EASE_SPRING} forwards;
  margin-bottom: 1.5rem;
}}

.capabl-cmd-result-item {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.55rem 0.85rem;
  border-radius: {RADIUS.RADIUS_XS};
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid {COLORS.BORDER_HAIRLINE};
  margin-bottom: 0.35rem;
  transition: all {MOTION.DURATION_FAST} {MOTION.EASE_SMOOTH_OUT};
  cursor: pointer;
}}

.capabl-cmd-result-item:hover {{
  background: {COLORS.BRAND_SURFACE};
  border-color: {COLORS.BRAND_BORDER};
  transform: translateX(3px);
}}

/* -----------------------------------------------------------------------------
   PHASE 11: SECURITY & TRUST CENTER STYLES
   ----------------------------------------------------------------------------- */
.capabl-security-card {{
  background: {COLORS.SURFACE_GLASS};
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid {COLORS.BORDER_MUTED};
  border-radius: {RADIUS.RADIUS_MD};
  padding: 1.25rem;
  box-shadow: {ELEVATION.SHADOW_LOW};
  transition: all {MOTION.DURATION_FAST} {MOTION.EASE_SPRING};
  height: 100%;
}}

.capabl-security-card:hover {{
  transform: translateY(-3px);
  border-color: rgba(16, 185, 129, 0.45) !important;
  box-shadow: 0 16px 36px -6px rgba(0, 0, 0, 0.75), 0 0 20px -2px rgba(16, 185, 129, 0.25) !important;
}}

.capabl-security-card-active {{
  border-color: rgba(16, 185, 129, 0.5) !important;
  background: rgba(16, 185, 129, 0.04) !important;
}}

.capabl-security-badge-shield {{
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.85rem;
  border-radius: 9999px;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: #34D399;
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  box-shadow: 0 0 12px -2px rgba(16, 185, 129, 0.2);
}}

.capabl-security-badge-locked {{
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.85rem;
  border-radius: 9999px;
  background: rgba(6, 182, 212, 0.12);
  border: 1px solid rgba(6, 182, 212, 0.35);
  color: #22D3EE;
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}

.capabl-audit-timeline-container {{
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1rem;
}}

.capabl-audit-event-row {{
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: {RADIUS.RADIUS_SM};
  padding: 1rem 1.25rem;
  transition: all {MOTION.DURATION_FAST} {MOTION.EASE_SPRING};
  animation: capablTimelineNodeEnter 0.4s var(--capabl-ease-spring) both;
}}

.capabl-audit-event-row:hover {{
  background: rgba(30, 41, 59, 0.85);
  border-color: rgba(99, 102, 241, 0.4);
  transform: translateX(4px);
  box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.5);
}}

.capabl-security-drawer {{
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(99, 102, 241, 0.45);
  border-radius: {RADIUS.RADIUS_LG};
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 20px 48px -8px rgba(0, 0, 0, 0.85), 0 0 32px -4px rgba(99, 102, 241, 0.25);
  animation: capablSecurityDrawerOpen 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
}}

.capabl-redaction-pill {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: 4px;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: #34D399;
  font-size: 0.74rem;
  font-weight: 600;
}}

.capabl-actor-pill {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.35);
  color: #A5B4FC;
  font-size: 0.75rem;
  font-weight: 600;
}}

.capabl-resource-pill {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.35);
  color: #FCD34D;
  font-size: 0.75rem;
  font-weight: 600;
}}

/* -----------------------------------------------------------------------------
   PHASE 12: RECRUITMENT ANALYTICS & VISUALIZATION STYLES
   ----------------------------------------------------------------------------- */
.capabl-chart-container {{
  position: relative;
  background: rgba(18, 24, 38, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
  backdrop-filter: blur(16px);
  animation: capablChartEnter 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.capabl-analytics-kpi-card {{
  background: rgba(18, 24, 38, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 1.15rem 1.25rem;
  transition: transform 0.2s ease, border-color 0.2s ease;
  animation: capablCardEnter 0.4s ease forwards;
}}

.capabl-analytics-kpi-card:hover {{
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.35);
}}

.capabl-insufficient-data-box {{
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.25rem 1.5rem;
  text-align: center;
  background: rgba(18, 24, 38, 0.45);
  border: 1px dashed rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  margin: 0.75rem 0;
}}

.capabl-insufficient-data-box .not-enough-title {{
  font-size: 0.95rem;
  font-weight: 700;
  color: #F8FAFC;
  margin-top: 0.4rem;
  margin-bottom: 0.2rem;
}}

.capabl-insufficient-data-box .not-enough-caption {{
  font-size: 0.8rem;
  color: #94A3B8;
  max-width: 440px;
  line-height: 1.45;
}}

/* -----------------------------------------------------------------------------
   MOBILE NAVIGATION DRAWER RESPONSIVENESS
   ----------------------------------------------------------------------------- */
@media (max-width: 768px) {{
  [data-testid="stSidebar"] {{
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    height: 100vh !important;
    z-index: 99999 !important;
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.8) !important;
    transition: transform {MOTION.DURATION_STANDARD} {MOTION.EASE_SPRING} !important;
  }}
  .capabl-topbar {{
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }}
}}
</style>
"""


def inject_theme() -> None:
    """Injects the complete production theme and motion stylesheet into the active Streamlit app."""
    css = generate_theme_css()
    st.markdown(css, unsafe_allow_html=True)
