"""Streamlit entrypoints for the brand mark."""

from __future__ import annotations

import streamlit as st

from components.shared.logo.svg import build_animated_document, sidebar_logo_uris


def _theme_base() -> str:
    """Return ``light`` or ``dark`` from the active Streamlit theme."""
    theme = st.context.theme
    value = getattr(theme, "type", None)
    if isinstance(theme, dict):
        value = theme.get("type")
    return value if value in ("light", "dark") else "light"


def apply_sidebar_logo(*, size: str = "large") -> None:
    """Static top-left wordmark/icon. Green inks per surface + theme."""
    wordmark, icon = sidebar_logo_uris(theme=_theme_base())
    st.logo(wordmark, icon_image=icon, size=size)
    st.html("<style>img.stLogo{height:3rem!important}</style>")


def render_logo(*, width: int = 300, animated: bool = True, height: int = 270) -> None:
    """Animated Home mark only (unchanged primary ink)."""
    st.iframe(
        build_animated_document(width=width, animated=animated),
        height=height,
        width="stretch",
    )
