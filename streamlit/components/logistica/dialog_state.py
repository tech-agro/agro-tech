"""Controle do estado de abertura dos dialogos do modulo de logistica.

Varias entidades independentes (operacoes, veiculos, tipos, rotas, cargas)
usam escopo (`scope`) para nao interferir entre abas.
"""

from __future__ import annotations

import streamlit as st

_DIALOG_KEY_PREFIX = "logistica_dialog"


def _dialog_key(scope: str) -> str:
    return f"{_DIALOG_KEY_PREFIX}_{scope}"


def open_dialog(scope: str, kind: str, entity_id: int | None = None) -> None:
    key = _dialog_key(scope)
    target = (kind, entity_id)
    if st.session_state.get(key) != target:
        st.session_state[key] = target


def get_dialog(scope: str) -> tuple[str, int | None] | None:
    return st.session_state.get(_dialog_key(scope))


def clear_dialog_state(scope: str, entity_id: int | None = None) -> None:
    st.session_state.pop(_dialog_key(scope), None)
    if entity_id is not None:
        st.session_state.pop(f"{scope}_editor_{entity_id}", None)
        st.session_state.pop(f"edit_operation_loads_{entity_id}", None)
        st.session_state.pop(f"edit_operation_loads_editor_{entity_id}", None)
        st.session_state.pop(f"_init_edit_operation_loads_editor_{entity_id}", None)
        st.session_state.pop(f"edit_operation_loads_{entity_id}_prev", None)
    if scope == "operacoes":
        for key in (
            "new_operation_loads",
            "new_operation_loads_editor",
            "_init_new_operation_loads_editor",
            "new_operation_loads_prev",
        ):
            st.session_state.pop(key, None)
