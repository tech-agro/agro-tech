"""Scoped dialog state for the Manutencao module."""

from __future__ import annotations

import streamlit as st

_DIALOG_KEY_PREFIX = "manutencao_dialog"


def _dialog_key(scope: str) -> str:
    return f"{_DIALOG_KEY_PREFIX}_{scope}"


def open_dialog(scope: str, kind: str, entity_id: int | None = None) -> None:
    key = _dialog_key(scope)
    target = (kind, entity_id)
    if st.session_state.get(key) == target:
        return
    if kind == "create" and scope == "prestadores":
        st.session_state.pop(f"_novo_prestador_cnpj_data_{scope}", None)
    st.session_state[key] = target


def get_dialog(scope: str) -> tuple[str, int | None] | None:
    return st.session_state.get(_dialog_key(scope))


def clear_dialog_state(scope: str, entity_id: int | None = None) -> None:
    st.session_state.pop(_dialog_key(scope), None)
    if scope == "prestadores":
        st.session_state.pop(f"_novo_prestador_cnpj_data_{scope}", None)
