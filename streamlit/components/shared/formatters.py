"""Shared display helpers for Streamlit screens."""

from __future__ import annotations

import pandas as pd


def format_money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_int_or_dash(value: float | int | None) -> str:
    """Integer id/count, or an em dash for missing values (see format_money_or_dash)."""
    if value is None or is_blank(value):
        return "—"
    return str(int(value))


def format_number_or_dash(value: float | None, decimals: int = 2) -> str:
    """BR-formatted number, or an em dash for missing values (see format_money_or_dash)."""
    if value is None or is_blank(value):
        return "—"
    texto = f"{float(value):,.{decimals}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def format_money_or_dash(value: float | None) -> str:
    """format_money, but safe for optional values.

    Streamlit's dataframe NumberColumn renders a missing value as the
    literal text "None" instead of a blank cell, so any column that can be
    legitimately absent (no data yet, not applicable) must be pre-formatted
    as text rather than left as a numeric NaN for column_config to handle.
    """
    if value is None or is_blank(value):
        return "—"
    return format_money(float(value))


def is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, (pd.Series, pd.DataFrame, list, tuple, dict)):
        return True
    try:
        result = pd.isna(value)
    except (ValueError, TypeError):
        return False
    if isinstance(result, (pd.Series, pd.DataFrame)):
        return True
    return bool(result)
