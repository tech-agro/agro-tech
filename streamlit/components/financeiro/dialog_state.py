"""Controle do estado dos diálogos do módulo financeiro."""

from __future__ import annotations

import streamlit as st

_DIALOG_KEY_PREFIX = "financeiro_dialog"


def _dialog_key(scope: str) -> str:
    return f"{_DIALOG_KEY_PREFIX}_{scope}"


def open_dialog(
    scope: str,
    kind: str,
    entity_id: int | None = None,
) -> None:
    """Abre um diálogo para o escopo informado."""
    key = _dialog_key(scope)
    target = (kind, entity_id)

    if st.session_state.get(key) != target:
        st.session_state[key] = target


def get_dialog(
    scope: str,
) -> tuple[str, int | None] | None:
    """Retorna (tipo, id) do diálogo aberto para o escopo informado."""
    return st.session_state.get(_dialog_key(scope))


def clear_dialog_state(
    scope: str,
    entity_id: int | None = None,
) -> None:
    """Fecha o diálogo do escopo informado."""
    st.session_state.pop(_dialog_key(scope), None)

    if entity_id is not None:
        st.session_state.pop(f"{scope}_editor_{entity_id}", None)