"""Reusable theme-aware chart helpers (Altair) shared across modules."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


def is_dark_theme() -> bool:
    return bool(
        hasattr(st, "context")
        and hasattr(st.context, "theme")
        and st.context.theme.type == "dark"
    )


def trend_chart(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    color_field: str | None = None,
    y_title: str | None = None,
    height: int = 220,
    palette: tuple[str, ...] = ("#0E8C7D", "#C9861E", "#4B7BEC"),
) -> None:
    """Line chart with points, theme-aware palette for up to a few series."""
    if df.empty:
        st.info("Sem dados para exibir.")
        return

    encode_kwargs = {
        "x": alt.X(f"{x}:T", title=None),
        "y": alt.Y(f"{y}:Q", title=y_title or y),
    }
    tooltip = [alt.Tooltip(f"{x}:T", title="Data"), alt.Tooltip(f"{y}:Q", title=y_title or y)]
    if color_field:
        encode_kwargs["color"] = alt.Color(
            f"{color_field}:N",
            title=None,
            scale=alt.Scale(range=list(palette)),
            legend=alt.Legend(orient="top"),
        )
        tooltip.append(alt.Tooltip(f"{color_field}:N", title="Serie"))
    encode_kwargs["tooltip"] = tooltip

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(**encode_kwargs)
        .properties(height=height)
    )
    st.altair_chart(chart)
