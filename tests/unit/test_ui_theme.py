"""
Unit Tests for CAPABL UI Theme & Motion Engine (Phase 1).

Validates:
1. Design Tokens: Colors, Typography, Spacing, Radius, Elevation, Motion.
2. 17 Centralized Motion Primitives:
   - Page enter/exit, card enter, list stagger, modal enter, drawer enter,
     tooltip, hover elevation, button press, loading shimmer, success glow,
     error attention, status pulse, evidence reveal, agent activity pulse.
3. Micro-Interactions:
   - Button hover/press scaling, card hover depth, status dot pulses.
4. Accessibility:
   - prefers-reduced-motion media query and override rules.
5. Master Theme Stylesheet:
   - Ambient gradient, glassmorphic surfaces, widget overrides, semantic chips.
"""

import unittest
from capabl_core.ui.theme.tokens import (
    ColorTokens,
    TypographyTokens,
    SpacingTokens,
    RadiusTokens,
    ElevationTokens,
    MotionTokens,
    COLORS,
    TYPOGRAPHY,
    SPACING,
    RADIUS,
    ELEVATION,
    MOTION,
)
from capabl_core.ui.theme.motion import generate_motion_css
from capabl_core.ui.theme.styles import generate_theme_css, inject_theme


class TestCAPABLDesignTokens(unittest.TestCase):
    """Test suite for design tokens."""

    def test_color_tokens(self):
        self.assertEqual(COLORS.CANVAS_BASE, "#080B11")
        self.assertTrue(COLORS.SURFACE_GLASS.startswith("rgba"))
        self.assertTrue(COLORS.BORDER_HAIRLINE.startswith("rgba"))
        self.assertEqual(COLORS.TEXT_PRIMARY, "#F8FAFC")
        self.assertEqual(COLORS.BRAND_PRIMARY, "#6366F1")
        self.assertEqual(COLORS.CYAN_PRIMARY, "#06B6D4")
        self.assertEqual(COLORS.SUCCESS_PRIMARY, "#10B981")
        self.assertEqual(COLORS.DANGER_PRIMARY, "#F43F5E")
        self.assertEqual(COLORS.WARNING_PRIMARY, "#F59E0B")

    def test_typography_tokens(self):
        self.assertIn("Plus Jakarta Sans", TYPOGRAPHY.FONT_FAMILY_SANS)
        self.assertIn("JetBrains Mono", TYPOGRAPHY.FONT_FAMILY_MONO)
        self.assertTrue(TYPOGRAPHY.SIZE_XS.endswith("rem"))
        self.assertTrue(TYPOGRAPHY.SIZE_BASE.endswith("rem"))
        self.assertTrue(TYPOGRAPHY.SIZE_2XL.endswith("rem"))

    def test_spacing_and_radius_tokens(self):
        self.assertEqual(SPACING.SPACE_XS, "8px")
        self.assertEqual(SPACING.SPACE_MD, "16px")
        self.assertEqual(SPACING.SPACE_XL, "24px")
        self.assertEqual(RADIUS.RADIUS_SM, "8px")
        self.assertEqual(RADIUS.RADIUS_MD, "12px")
        self.assertEqual(RADIUS.RADIUS_FULL, "9999px")

    def test_elevation_tokens(self):
        self.assertIn("rgba", ELEVATION.SHADOW_LOW)
        self.assertIn("rgba", ELEVATION.SHADOW_MEDIUM)
        self.assertIn("rgba", ELEVATION.SHADOW_HIGH)
        self.assertIn("rgba(99, 102, 241", ELEVATION.SHADOW_BRAND_GLOW)
        self.assertIn("rgba(16, 185, 129", ELEVATION.SHADOW_SUCCESS_GLOW)

    def test_motion_tokens(self):
        self.assertEqual(MOTION.DURATION_FAST, "180ms")
        self.assertEqual(MOTION.DURATION_STANDARD, "300ms")
        self.assertEqual(MOTION.DURATION_COMPLEX, "480ms")
        self.assertTrue(MOTION.EASE_SPRING.startswith("cubic-bezier"))


class TestCAPABLMotionSystem(unittest.TestCase):
    """Test suite for motion engine and animation primitives."""

    def setUp(self):
        self.css = generate_motion_css()

    def test_motion_css_variables(self):
        self.assertIn("--capabl-ease-spring:", self.css)
        self.assertIn("--capabl-dur-fast:", self.css)
        self.assertIn("--capabl-dur-standard:", self.css)

    def test_17_motion_primitives_present(self):
        # 1 & 2: page enter / exit
        self.assertIn("keyframes capablPageEnter", self.css)
        self.assertIn("keyframes capablPageExit", self.css)
        self.assertIn(".motion-page-enter", self.css)

        # 3: card enter
        self.assertIn("keyframes capablCardEnter", self.css)
        self.assertIn(".motion-card-enter", self.css)

        # 4: list stagger
        self.assertIn(".stagger-1", self.css)
        self.assertIn(".stagger-2", self.css)
        self.assertIn(".stagger-6", self.css)

        # 5: modal enter
        self.assertIn("keyframes capablModalEnter", self.css)
        self.assertIn(".motion-modal-enter", self.css)

        # 6: drawer enter
        self.assertIn("keyframes capablDrawerEnter", self.css)
        self.assertIn(".motion-drawer-enter", self.css)

        # 7: tooltip pop
        self.assertIn("keyframes capablTooltipPop", self.css)

        # 8: hover elevation
        self.assertIn(".capabl-card-interactive:hover", self.css)
        self.assertIn("translateY(-2px)", self.css)

        # 9: button press
        self.assertIn("button:active", self.css)
        self.assertIn("scale(0.98)", self.css)

        # 10: loading shimmer
        self.assertIn("keyframes capablShimmer", self.css)
        self.assertIn(".capabl-skeleton", self.css)

        # 11: success confirmation
        self.assertIn("keyframes capablSuccessGlow", self.css)
        self.assertIn(".motion-success-flash", self.css)

        # 12: error attention
        self.assertIn("keyframes capablErrorAttention", self.css)
        self.assertIn(".motion-error-shake", self.css)

        # 13: status pulse
        self.assertIn("keyframes capablStatusPulse", self.css)
        self.assertIn(".capabl-status-dot-active", self.css)

        # 14 & 15: progress & evidence reveal
        self.assertIn("keyframes capablEvidenceReveal", self.css)
        self.assertIn(".motion-evidence-reveal", self.css)

        # 16: agent cognitive activity pulse
        self.assertIn("keyframes capablAgentPulse", self.css)
        self.assertIn(".motion-agent-active", self.css)

    def test_reduced_motion_accessibility(self):
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)
        self.assertIn("animation-duration: 0.01ms !important;", self.css)
        self.assertIn("transition-duration: 0.01ms !important;", self.css)
        self.assertIn(".capabl-status-dot-active", self.css)


class TestCAPABLMasterThemeStyles(unittest.TestCase):
    """Test suite for theme CSS generation and injection."""

    def setUp(self):
        self.css = generate_theme_css()

    def test_google_fonts_import(self):
        self.assertIn("Plus+Jakarta+Sans", self.css)
        self.assertIn("JetBrains+Mono", self.css)

    def test_ambient_canvas_and_surfaces(self):
        self.assertIn(COLORS.CANVAS_BASE, self.css)
        self.assertIn("radial-gradient", self.css)
        self.assertIn(".capabl-glass-card", self.css)
        self.assertIn(".capabl-glass-card-elevated", self.css)
        self.assertIn(".capabl-kpi-card", self.css)

    def test_semantic_skill_chips(self):
        self.assertIn(".capabl-chip-match", self.css)
        self.assertIn(".capabl-chip-gap", self.css)
        self.assertIn(".capabl-chip-neutral", self.css)

    def test_streamlit_widget_overrides(self):
        self.assertIn('[data-testid="stAppViewContainer"]', self.css)
        self.assertIn('[data-testid="stSidebar"]', self.css)
        self.assertIn('[data-testid="stBaseButton-primary"]', self.css)
        self.assertIn('[data-testid="stFileUploader"]', self.css)
        self.assertIn('[data-testid="stMetric"]', self.css)
        self.assertIn('.stTabs', self.css)


if __name__ == "__main__":
    unittest.main()
