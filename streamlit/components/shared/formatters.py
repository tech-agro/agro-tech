"""Shared display helpers for Streamlit screens."""

from __future__ import annotations

import pandas as pd


def format_money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
