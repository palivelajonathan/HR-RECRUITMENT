"""
Design Tokens for CAPABL Recruitment Intelligence OS.

Phase 1: Premium Visual Language & Motion System.
Defines foundational design constants: color palette, depth, elevation,
typography scales, border radii, spacing, and transition timing.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class ColorTokens:
    # Canvas & Surface
    CANVAS_BASE: str = "#080B11"
    SURFACE_SUBTLE: str = "#0C1019"
    SURFACE_RAISED: str = "#121824"
    SURFACE_GLASS: str = "rgba(18, 24, 38, 0.72)"
    SURFACE_OVERLAY: str = "rgba(22, 30, 48, 0.85)"
    SURFACE_HOVER: str = "rgba(255, 255, 255, 0.03)"
    
    # Borders & Dividers
    BORDER_HAIRLINE: str = "rgba(255, 255, 255, 0.05)"
    BORDER_MUTED: str = "rgba(255, 255, 255, 0.09)"
    BORDER_PROMINENT: str = "rgba(255, 255, 255, 0.16)"
    BORDER_FOCUS: str = "rgba(99, 102, 241, 0.5)"
    BORDER_GLOW: str = "rgba(99, 102, 241, 0.25)"

    # Typography
    TEXT_PRIMARY: str = "#F8FAFC"
    TEXT_SECONDARY: str = "#94A3B8"
    TEXT_MUTED: str = "#64748B"
    TEXT_FAINT: str = "#475569"
    TEXT_INVERSE: str = "#080B11"

    # Semantic - Primary / Action (Indigo / Iris)
    BRAND_PRIMARY: str = "#6366F1"
    BRAND_HOVER: str = "#4F46E5"
    BRAND_SURFACE: str = "rgba(99, 102, 241, 0.12)"
    BRAND_BORDER: str = "rgba(99, 102, 241, 0.3)"
    BRAND_GLOW: str = "rgba(99, 102, 241, 0.25)"

    # Semantic - Telemetry / AI Intel (Cyber Cyan)
    CYAN_PRIMARY: str = "#06B6D4"
    CYAN_SURFACE: str = "rgba(6, 182, 212, 0.10)"
    CYAN_BORDER: str = "rgba(6, 182, 212, 0.25)"
    CYAN_GLOW: str = "rgba(6, 182, 212, 0.25)"

    # Semantic - Match / Verified (Emerald Mint)
    SUCCESS_PRIMARY: str = "#10B981"
    SUCCESS_LIGHT: str = "#34D399"
    SUCCESS_SURFACE: str = "rgba(16, 185, 129, 0.10)"
    SUCCESS_BORDER: str = "rgba(16, 185, 129, 0.28)"
    SUCCESS_GLOW: str = "rgba(16, 185, 129, 0.20)"

    # Semantic - Missing / Gap (Coral Rose)
    DANGER_PRIMARY: str = "#F43F5E"
    DANGER_LIGHT: str = "#FB7185"
    DANGER_SURFACE: str = "rgba(244, 63, 94, 0.10)"
    DANGER_BORDER: str = "rgba(244, 63, 94, 0.28)"
    DANGER_GLOW: str = "rgba(244, 63, 94, 0.20)"

    # Semantic - Gatekeeper / Attention (Amber Gold)
    WARNING_PRIMARY: str = "#F59E0B"
    WARNING_LIGHT: str = "#FBBF24"
    WARNING_SURFACE: str = "rgba(245, 158, 11, 0.10)"
    WARNING_BORDER: str = "rgba(245, 158, 11, 0.28)"
    WARNING_GLOW: str = "rgba(245, 158, 11, 0.20)"


@dataclass(frozen=True)
class TypographyTokens:
    FONT_FAMILY_SANS: str = "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    FONT_FAMILY_MONO: str = "'JetBrains Mono', 'Fira Code', Menlo, Consolas, monospace"
    
    # Font Sizes
    SIZE_2XS: str = "0.70rem"   # 11.2px
    SIZE_XS: str = "0.75rem"    # 12px
    SIZE_SM: str = "0.85rem"    # 13.6px
    SIZE_BASE: str = "0.95rem"  # 15.2px
    SIZE_LG: str = "1.05rem"    # 16.8px
    SIZE_XL: str = "1.25rem"    # 20px
    SIZE_2XL: str = "1.50rem"   # 24px
    SIZE_3XL: str = "1.875rem"  # 30px
    SIZE_4XL: str = "2.25rem"   # 36px


@dataclass(frozen=True)
class SpacingTokens:
    SPACE_2XS: str = "4px"
    SPACE_XS: str = "8px"
    SPACE_SM: str = "12px"
    SPACE_MD: str = "16px"
    SPACE_LG: str = "20px"
    SPACE_XL: str = "24px"
    SPACE_2XL: str = "32px"
    SPACE_3XL: str = "48px"
    SPACE_4XL: str = "64px"


@dataclass(frozen=True)
class RadiusTokens:
    RADIUS_XS: str = "4px"
    RADIUS_SM: str = "8px"
    RADIUS_MD: str = "12px"
    RADIUS_LG: str = "16px"
    RADIUS_XL: str = "22px"
    RADIUS_FULL: str = "9999px"


@dataclass(frozen=True)
class ElevationTokens:
    SHADOW_FLAT: str = "none"
    SHADOW_LOW: str = "0 2px 8px -1px rgba(0, 0, 0, 0.4)"
    SHADOW_MEDIUM: str = "0 8px 24px -4px rgba(0, 0, 0, 0.5), 0 2px 6px -1px rgba(0, 0, 0, 0.3)"
    SHADOW_HIGH: str = "0 20px 40px -8px rgba(0, 0, 0, 0.65), 0 4px 12px rgba(0, 0, 0, 0.4)"
    SHADOW_BRAND_GLOW: str = "0 0 24px -2px rgba(99, 102, 241, 0.18)"
    SHADOW_SUCCESS_GLOW: str = "0 0 20px -2px rgba(16, 185, 129, 0.22)"
    SHADOW_DANGER_GLOW: str = "0 0 20px -2px rgba(244, 63, 94, 0.22)"


@dataclass(frozen=True)
class MotionTokens:
    # Durations
    DURATION_INSTANT: str = "100ms"
    DURATION_FAST: str = "180ms"
    DURATION_STANDARD: str = "300ms"
    DURATION_COMPLEX: str = "480ms"
    DURATION_LONG: str = "650ms"

    # Easings
    EASE_SPRING: str = "cubic-bezier(0.16, 1, 0.3, 1)"
    EASE_SMOOTH_OUT: str = "cubic-bezier(0.2, 0.8, 0.2, 1)"
    EASE_SHARP: str = "cubic-bezier(0.4, 0, 0.2, 1)"


COLORS = ColorTokens()
TYPOGRAPHY = TypographyTokens()
SPACING = SpacingTokens()
RADIUS = RadiusTokens()
ELEVATION = ElevationTokens()
MOTION = MotionTokens()
