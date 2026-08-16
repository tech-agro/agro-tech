"""Session-state helpers for purchases dialogs (scoped by tab/entity)."""

from __future__ import annotations

import streamlit as st

_DIALOG_KEY_PREFIX = "compras_dialog"

# Backward-compatible alias used by older order dialogs.
DIALOG_KEY = f"{_DIALOG_KEY_PREFIX}_pedidos"


def _dialog_key(scope: str) -> str:
    return f"{_DIALOG_KEY_PREFIX}_{scope}"


def open_dialog(scope: str, kind: str, entity_id: int | None = None) -> None:
    """Open a dialog for the given scope (e.g. pedidos, fornecedores)."""
    key = _dialog_key(scope)
    target = (kind, entity_id)
    if st.session_state.get(key) == target:
        return

    if scope == "pedidos":
        if kind == "new":
            for item in (
                "new_order_items",
                "new_order_items_editor",
                "_init_new_order_items_editor",
                "new_order_items_prev",
            ):
                st.session_state.pop(item, None)
        if kind == "edit" and entity_id is not None:
            st.session_state.pop(f"edit_order_items_{entity_id}", None)
            st.session_state.pop(f"edit_order_items_editor_{entity_id}", None)
            st.session_state.pop(f"_init_edit_order_items_editor_{entity_id}", None)
            st.session_state.pop(f"edit_order_items_{entity_id}_prev", None)

    if scope == "fornecedores" and kind == "create":
        st.session_state.pop(f"_novo_fornecedor_cnpj_data_{scope}", None)

    if scope == "solicitacoes":
        if kind == "new":
            for item in (
                "new_request_items",
                "new_request_items_editor",
                "_init_new_request_items_editor",
                "new_request_items_prev",
            ):
                st.session_state.pop(item, None)
        if kind == "edit" and entity_id is not None:
            prefix = f"edit_request_items_{entity_id}"
            for item in (
                prefix,
                f"{prefix}_editor",
                f"_init_{prefix}_editor",
                f"{prefix}_prev",
            ):
                st.session_state.pop(item, None)

    st.session_state[key] = target


def get_dialog(scope: str) -> tuple[str, int | None] | None:
    return st.session_state.get(_dialog_key(scope))


def clear_dialog_state(scope: str, entity_id: int | None = None) -> None:
    st.session_state.pop(_dialog_key(scope), None)

    if scope == "pedidos":
        for item in (
            "new_order_items",
            "new_order_items_editor",
            "_init_new_order_items_editor",
            "new_order_items_prev",
        ):
            st.session_state.pop(item, None)
        if entity_id is not None:
            st.session_state.pop(f"edit_order_items_{entity_id}", None)
            st.session_state.pop(f"edit_order_items_editor_{entity_id}", None)
            st.session_state.pop(f"_init_edit_order_items_editor_{entity_id}", None)
            st.session_state.pop(f"edit_order_items_{entity_id}_prev", None)

    if scope == "fornecedores":
        st.session_state.pop(f"_novo_fornecedor_cnpj_data_{scope}", None)

    if scope == "solicitacoes" and entity_id is not None:
        prefix = f"edit_request_items_{entity_id}"
        for item in (
            prefix,
            f"{prefix}_editor",
            f"_init_{prefix}_editor",
            f"{prefix}_prev",
        ):
            st.session_state.pop(item, None)
