"""Diálogos da entidade Local de Armazenamento."""

from __future__ import annotations

from decimal import Decimal

import streamlit as st

from app.estoque.schemas.local_armazenamento import (
    LocalArmazenamentoCreateSchema,
    LocalArmazenamentoUpdateSchema,
)
from components.estoque.dialog_state import clear_dialog_state, get_dialog
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

        elif kind == "edit":
            _edit_dialog(scope, entity_id)

        elif kind == "delete":
            _delete_dialog(scope, entity_id)


@st.dialog("Novo local de armazenamento", width="large")
def _create_dialog(scope: str) -> None:
    descricao = st.text_input("Descrição")

    capacidade = st.number_input(
        "Capacidade",
        min_value=0.0,
        step=1.0,
        format="%.2f",
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

    try:
        payload = LocalArmazenamentoCreateSchema(
            descricao=descricao,
            capacidade=Decimal(str(capacidade)) if capacidade > 0 else None,
        )

        client.create_local(payload)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return
    
    st.toast("Local criado com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes do local", width="large")
def _view_dialog(scope: str, id_local: int) -> None:
    try:
        local = client.get_local(id_local)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_local)
            st.rerun()

        return

    st.text_input("Descrição", local.descricao, disabled=True)

    st.text_input(
        "Capacidade",
        f"{local.capacidade:.2f}" if local.capacidade is not None else "-",
        disabled=True,
    )

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, id_local)
        st.rerun()


@st.dialog("Editar local", width="large")
def _edit_dialog(scope: str, id_local: int) -> None:
    try:
        local = client.get_local(id_local)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_local)
            st.rerun()

        return

    descricao = st.text_input(
        "Descrição",
        value=local.descricao,
    )

    capacidade = st.number_input(
        "Capacidade",
        value=float(local.capacidade or 0),
        min_value=0.0,
        step=1.0,
        format="%.2f",
    )

    col1, col2 = st.columns(2)

    with col1:
        salvar = st.button("Salvar", use_container_width=True)

    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, id_local)
        st.rerun()

    if not salvar:
        return

    payload = LocalArmazenamentoUpdateSchema(
        descricao=descricao,
        capacidade=Decimal(str(capacidade)) if capacidade > 0 else None,
    )

    try:
        client.update_local(id_local, payload)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_local)
            st.rerun()

        return
    
    st.toast("Local atualizado com sucesso.")
    clear_dialog_state(scope, id_local)
    st.rerun()


@st.dialog("Excluir local")
def _delete_dialog(scope: str, id_local: int) -> None:
    try:
        local = client.get_local(id_local)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_local)
            st.rerun()

        return

    st.warning(
        f"Deseja realmente excluir o local **{local.descricao}**?\n\n"
        "Essa ação não poderá ser desfeita."
    )

    col1, col2 = st.columns(2)

    with col1:
        excluir = st.button("Excluir", use_container_width=True)

    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, id_local)
        st.rerun()

    if not excluir:
        return

    try:
        client.delete_local(id_local)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_local)
            st.rerun()

        return

    st.toast("Local excluído com sucesso.")
    clear_dialog_state(scope, id_local)
    st.rerun()