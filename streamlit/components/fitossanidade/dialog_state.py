"""Controle do estado de abertura dos dialogos do modulo de fitossanidade.

Escopos independentes (controles, agentes) para nao interferir entre abas.
"""

from __future__ import annotations

import streamlit as st

_DIALOG_KEY_PREFIX = "fitossanidade_dialog"


def _dialog_key(scope: str) -> str:
    return f"{_DIALOG_KEY_PREFIX}_{scope}"


def open_dialog(scope: str, kind: str, entity_id: int | None = None) -> None:
    key = _dialog_key(scope)
    target = (kind, entity_id)
    if st.session_state.get(key) == target:
        return
    if kind == "create":
        clear_dialog_state(scope)
    if kind == "edit" and entity_id is not None and scope == "controles":
        clear_control_editors(entity_id)
    st.session_state[key] = target


def get_dialog(scope: str) -> tuple[str, int | None] | None:
    return st.session_state.get(_dialog_key(scope))


def clear_control_editors(control_id: int) -> None:
    for prefix in ("edit_control_occurrences", "edit_control_applications"):
        st.session_state.pop(f"{prefix}_{control_id}", None)
        st.session_state.pop(f"{prefix}_editor_{control_id}", None)
        st.session_state.pop(f"_init_{prefix}_editor_{control_id}", None)
        st.session_state.pop(f"{prefix}_{control_id}_prev", None)


def clear_dialog_state(scope: str, entity_id: int | None = None) -> None:
    st.session_state.pop(_dialog_key(scope), None)
    if scope == "controles":
        for key in (
            "new_control_occurrences",
            "new_control_occurrences_editor",
            "_init_new_control_occurrences_editor",
            "new_control_occurrences_prev",
            "new_control_applications",
            "new_control_applications_editor",
            "_init_new_control_applications_editor",
            "new_control_applications_prev",
        ):
            st.session_state.pop(key, None)
        if entity_id is not None:
            clear_control_editors(entity_id)
