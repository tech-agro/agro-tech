"""Central visual-identity tokens, mirroring `.streamlit/config.toml`.

Keep these in sync with the theme file so charts, badges and any
Styler-based highlighting always match the app's light/dark palettes.
"""

from __future__ import annotations

import streamlit as st

from components.shared.charts import is_dark_theme

BRAND_TEAL = "#245C53"
BRAND_TEAL_SOFT = "#2F8F83"

CATEGORICAL = (
    "#245C53",
    "#C9861E",
    "#4B7BEC",
    "#8E5FD1",
    "#2F8F83",
    "#D1495B",
    "#5A6B57",
)

_SEMANTIC_LIGHT = {
    "green": "#1B7A4B",
    "green_bg": "#E1F3E8",
    "red": "#C23B3B",
    "red_bg": "#FBE7E7",
    "orange": "#B5791A",
    "orange_bg": "#FBEED9",
    "blue": "#3462C9",
    "blue_bg": "#E4EBFA",
    "gray": "#5B6672",
    "gray_bg": "#E9ECEF",
}

_SEMANTIC_DARK = {
    "green": "#4ADE94",
    "green_bg": "#123024",
    "red": "#F0716C",
    "red_bg": "#33191A",
    "orange": "#E3A857",
    "orange_bg": "#33260F",
    "blue": "#6FA0F5",
    "blue_bg": "#152238",
    "gray": "#9AA6B2",
    "gray_bg": "#232B33",
}

# Status "tone" -> small colored indicator used as a text prefix in table
# cells, since inline colored badges are not renderable inside grid cells
# (only text/markdown-overlay is). Keeps status columns scannable at a glance.
STATUS_DOT = {
    "green": "\U0001f7e2",
    "red": "\U0001f534",
    "orange": "\U0001f7e0",
    "blue": "\U0001f535",
    "gray": "⚪",
}


def semantic(tone: str) -> str:
    """Hex color for a semantic tone ("green", "red", "orange", "blue", "gray")."""
    table = _SEMANTIC_DARK if is_dark_theme() else _SEMANTIC_LIGHT
    return table[tone]


def semantic_bg(tone: str) -> str:
    table = _SEMANTIC_DARK if is_dark_theme() else _SEMANTIC_LIGHT
    return table[f"{tone}_bg"]


def status_dot(tone: str) -> str:
    return STATUS_DOT.get(tone, STATUS_DOT["gray"])


def badge_value(label: str | None) -> list[str]:
    """Wrap a status label for `st.column_config.MultiselectColumn` pill rendering."""
    return [label] if label else []


def badge_column(label: str, options: list[str], tones: dict[str, str], **kwargs):
    """A read-only MultiselectColumn that renders each status as a colored pill.

    Pair with `badge_value()` when building the DataFrame column.
    """
    colors = [semantic(tones.get(opt, "gray")) for opt in options]
    return st.column_config.MultiselectColumn(
        label, options=options, color=colors, disabled=True, **kwargs
    )
