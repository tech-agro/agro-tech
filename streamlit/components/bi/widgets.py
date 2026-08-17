"""Shared BI widgets: CSV export and metric deltas."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd
import streamlit as st


def unit_label(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "value"):
        value = value.value
    text = str(value).strip()
    return text or None


def single_unit(units: set[str | None]) -> str | None:
    clean = {unit for unit in units if unit}
    if len(clean) == 1:
        return next(iter(clean))
    return None


def fmt_qty(value: float) -> str:
    texto = f"{value:,.1f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(value: float) -> str:
    return str(int(round(value)))


def fmt_brl(value: float) -> str:
    texto = f"{value:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def download_csv(df: pd.DataFrame, *, filename: str, key: str) -> None:
    st.download_button(
        "Baixar CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        icon=":material/download:",
        key=key,
    )


def delta_label(
    current: float | int | None,
    previous: float | int | None,
    *,
    formatter: Callable[[float], str],
) -> str | None:
    if current is None or previous is None:
        return None
    diff = float(current) - float(previous)
    if abs(diff) < 1e-9:
        return f"{formatter(0.0)} vs periodo anterior"
    sign = "+" if diff > 0 else ""
    return f"{sign}{formatter(diff)} vs periodo anterior"
