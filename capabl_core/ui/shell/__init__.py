"""
CAPABL UI Production Application Shell.

Phase 2: Production Application Shell & Navigation.
"""

from capabl_core.ui.shell.sidebar import render_sidebar, NAV_PRIMARY, NAV_SECONDARY
from capabl_core.ui.shell.topbar import render_topbar
from capabl_core.ui.shell.command_palette import render_command_palette

__all__ = [
    "render_sidebar",
    "render_topbar",
    "render_command_palette",
    "NAV_PRIMARY",
    "NAV_SECONDARY",
]
