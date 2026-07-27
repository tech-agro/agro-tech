"""Diálogos da entidade Lote."""

from __future__ import annotations

import streamlit as st

from app.estoque.enum import StatusLote
from app.estoque.schemas.lote import LoteUpdateSchema
from components.estoque.dialog_state import clear_dialog_state, get_dialog
from services.estoque_client import EstoqueApiError, EstoqueClient


client = EstoqueClient()

_STATUS_LABELS = {
    StatusLote.EM_ANALISE: "Em análise",
    StatusLote.LIBERADO: "Liberado",
    StatusLote.BLOQUEADO: "Bloqueado",
}


def render(scope: str) -> None:
    """Renderiza o diálogo atualmente aberto."""
    dialog = get_dialog(scope)
    
    if dialog is None:
        return

    kind, entity_id = dialog

    if entity_id is None:
        return

    if kind == "view":
        _view_dialog(scope, entity_id)

    elif kind == "edit":
        _edit_dialog(scope, entity_id)

    elif kind == "delete":
        _delete_dialog(scope, entity_id)


@st.dialog("Detalhes do lote", width="large")
def _view_dialog(scope: str, id_lote: int) -> None:
    try:
        lote = client.get_lote(id_lote)
    except EstoqueApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope, id_lote)
            st.rerun()
        return

    st.text_input("Código", lote.codigo_lote, disabled=True)
    st.text_input("Produto", lote.produto_nome or "-", disabled=True)
    st.text_input(
        "Validade",
        lote.validade.strftime("%d/%m/%Y") if lote.validade else "",
        disabled=True,
    )
    st.text_input("Qualidade", lote.qualidade or "", disabled=True)
    st.text_input("Status", _STATUS_LABELS.get(lote.status, lote.status.value), disabled=True)

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, id_lote)
        st.rerun()


@st.dialog("Editar lote", width="large")
def _edit_dialog(scope: str, id_lote: int) -> None:
    try:
        lote = client.get_lote(id_lote)
    except EstoqueApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope, id_lote)
            st.rerun()
        return

    validade = st.date_input(
        "Validade",
        value=lote.validade,
    )

    qualidade = st.text_input(
        "Qualidade",
        value=lote.qualidade or "",
    )

    status = st.selectbox(
        "Status",
        options=list(StatusLote),
        index=list(StatusLote).index(lote.status),
        format_func=lambda s: _STATUS_LABELS.get(s, s.value),
    )

    col1, col2 = st.columns(2)

    with col1:
        salvar = st.button(
            "Salvar",
            use_container_width=True,
        )

    with col2:
        cancelar = st.button(
            "Cancelar",
            use_container_width=True,
        )

    if cancelar:
        clear_dialog_state(scope, id_lote)
        st.rerun()

    if salvar:
        payload = LoteUpdateSchema(
            validade=validade,
            qualidade=qualidade.strip() or None,
            status=status,
        )

        try:
            client.update_lote(id_lote, payload)
        except EstoqueApiError as exc:
            st.error(exc.user_message)
            return

        st.toast("Lote atualizado com sucesso.")
        clear_dialog_state(scope, id_lote)
        st.rerun()


@st.dialog("Excluir lote")
def _delete_dialog(scope: str, id_lote: int) -> None:
    try:
        lote = client.get_lote(id_lote)
    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_lote)
            st.rerun()
        return

    st.warning(
        f"Deseja realmente excluir o lote **{lote.codigo_lote}**?\n\n"
        "Essa ação não poderá ser desfeita."
    )

    col1, col2 = st.columns(2)

    with col1:
        excluir = st.button("Excluir", use_container_width=True)

    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, id_lote)
        st.rerun()

    if not excluir:
        return

    try:
        client.delete_lote(id_lote)
    except EstoqueApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar", use_container_width=True):
            clear_dialog_state(scope, id_lote)
            st.rerun()
        return
    
    st.toast("Lote excluído com sucesso.")
    clear_dialog_state(scope, id_lote)
    st.rerun()