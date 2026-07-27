"""Session-state helpers for purchases dialogs."""

from __future__ import annotations

import streamlit as st

DIALOG_KEY = "compras_dialog"


def clear_dialog_state(order_id: int | None = None) -> None:
    st.session_state.pop(DIALOG_KEY, None)
    for key in (
        "new_order_items",
        "new_order_items_editor",
        "_init_new_order_items_editor",
        "new_order_items_prev",
    ):
        st.session_state.pop(key, None)
    if order_id is not None:
        st.session_state.pop(f"edit_order_items_{order_id}", None)
        st.session_state.pop(f"edit_order_items_editor_{order_id}", None)
        st.session_state.pop(f"_init_edit_order_items_editor_{order_id}", None)
        st.session_state.pop(f"edit_order_items_{order_id}_prev", None)


def open_dialog(kind: str, order_id: int | None = None) -> None:
    current = st.session_state.get(DIALOG_KEY)
    target = (kind, order_id)
    if current != target:
        if kind == "new":
            for key in (
                "new_order_items",
                "new_order_items_editor",
                "_init_new_order_items_editor",
                "new_order_items_prev",
            ):
                st.session_state.pop(key, None)
        if kind == "edit" and order_id is not None:
            st.session_state.pop(f"edit_order_items_{order_id}", None)
            st.session_state.pop(f"edit_order_items_editor_{order_id}", None)
            st.session_state.pop(f"_init_edit_order_items_editor_{order_id}", None)
            st.session_state.pop(f"edit_order_items_{order_id}_prev", None)
    st.session_state[DIALOG_KEY] = target
