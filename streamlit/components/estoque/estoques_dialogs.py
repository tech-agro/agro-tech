"""Diálogos da entidade Estoque."""

from __future__ import annotations

import streamlit as st

from app.estoque.schemas.estoque import EstoqueCreateSchema
from components.estoque.dialog_state import clear_dialog_state, get_dialog
from components.estoque.formatters import local_label
from services.estoque_client import EstoqueApiError, EstoqueClient


client = EstoqueClient()


def render(scope: str) -> None:
    """Renderiza o diálogo atualmente aberto."""
    dialog = get_dialog(scope)
    
    if dialog is None:
        return

    kind, entity_id = dialog

    if kind == "create":
        _create_dialog(scope)

    elif entity_id is not None:

        if kind == "view":
            _view_dialog(scope, entity_id)

        elif kind == "delete":
            _delete_dialog(scope, entity_id)


@st.dialog("Novo estoque", width="large")
def _create_dialog(scope: str) -> None:
    try:
        locais = client.list_local_options()

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    if not locais:
        st.info("Cadastre um local de armazenamento antes de criar um estoque.")

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    local = st.selectbox(
        "Local de armazenamento",
        options=locais,
        format_func=local_label,
    )

    col1, col2 = st.columns(2)

    with col1:
        salvar = st.button("Salvar", use_container_width=True)

    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope)
        st.rerun()

    if not salvar:
        return

    payload = EstoqueCreateSchema(
        id_local=local.id_local,
    )

    try:
        client.create_estoque(payload)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    st.toast("Estoque criado com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes do estoque", width="large")
def _view_dialog(scope: str, id_estoque: int) -> None:
    try:
        estoque = client.get_estoque(id_estoque)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_estoque)
            st.rerun()

        return

    st.text_input(
        "ID",
        str(estoque.id_estoque),
        disabled=True,
    )

    st.text_input(
        "Local de armazenamento",
        estoque.local_descricao or "-",
        disabled=True,
    )

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, id_estoque)
        st.rerun()


@st.dialog("Excluir estoque")
def _delete_dialog(scope: str, id_estoque: int) -> None:
    try:
        estoque = client.get_estoque(id_estoque)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_estoque)
            st.rerun()

        return

    st.warning(
        f"Deseja realmente excluir o estoque do local "
        f"**{estoque.local_descricao or '-'}**?\n\n"
        "Essa ação não poderá ser desfeita."
    )

    col1, col2 = st.columns(2)

    with col1:
        excluir = st.button("Excluir", use_container_width=True)

    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, id_estoque)
        st.rerun()

    if not excluir:
        return

    try:
        client.delete_estoque(id_estoque)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_estoque)
            st.rerun()

        return

    st.toast("Estoque excluído com sucesso.")
    clear_dialog_state(scope, id_estoque)
    st.rerun()