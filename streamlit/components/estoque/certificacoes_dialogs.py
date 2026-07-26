"""Diálogos da entidade Certificação de Lote."""

from __future__ import annotations

import streamlit as st

from app.core.enum import StatusCertificacao
from app.estoque.schemas.certificacao_lote import (
    CertificacaoLoteCreateSchema,
    CertificacaoLoteUpdateSchema,
)
from components.estoque.dialog_state import clear_dialog_state, get_dialog
from components.estoque.formatters import (
    certificacao_label,
    lote_label,
    STATUS_LABELS,
)
from services.estoque_client import EstoqueApiError, EstoqueClient
from pydantic import ValidationError


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


@st.dialog("Vincular certificação ao lote", width="large")
def _create_dialog(scope: str) -> None:
    try:
        certificacoes = client.list_certificacao_options()
        lotes = client.list_lote_options()

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    if not certificacoes:
        st.info("Cadastre uma certificação antes de realizar um vínculo.")

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    if not lotes:
        st.info("Cadastre um lote antes de realizar um vínculo.")

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    certificacao = st.selectbox(
        "Certificação",
        options=certificacoes,
        format_func=certificacao_label,
    )

    lote = st.selectbox(
        "Lote",
        options=lotes,
        format_func=lote_label,
    )

    dt_emissao = st.date_input(
        "Data de emissão",
        value=None,
    )

    dt_validade = st.date_input(
        "Data de validade",
        value=None,
    )

    numero_certificado = st.text_input("Número do certificado")

    status = st.selectbox(
        "Status",
        options=list(StatusCertificacao),
        format_func=lambda s: STATUS_LABELS[s],
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
        payload = CertificacaoLoteCreateSchema(
            id_certificacao=certificacao.id_certificacao,
            id_lote=lote.id_lote,
            dt_emissao=dt_emissao,
            dt_validade=dt_validade,
            numero_certificado=numero_certificado.strip() or None,
            status=status,
        )

        client.create_certificacao(payload)

    except (EstoqueApiError, ValidationError) as exc:
        message = exc.user_message if isinstance(exc, EstoqueApiError) else str(exc)
        st.error(message)

        if isinstance(exc, EstoqueApiError) and st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    st.toast("Certificação vinculada ao lote com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes da certificação do lote", width="large")
def _view_dialog(scope: str, id_certificacao: int) -> None:
    try:
        certificacao = client.get_certificacao(id_certificacao)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_certificacao)
            st.rerun()

        return

    st.text_input(
        "Certificação",
        certificacao.certificacao_nome or "-",
        disabled=True,
    )

    st.text_input(
        "Lote",
        certificacao.lote_codigo or "-",
        disabled=True,
    )

    st.text_input(
        "Data de emissão",
        certificacao.dt_emissao.strftime("%d/%m/%Y")
        if certificacao.dt_emissao
        else "-",
        disabled=True,
    )

    st.text_input(
        "Data de validade",
        certificacao.dt_validade.strftime("%d/%m/%Y")
        if certificacao.dt_validade
        else "-",
        disabled=True,
    )

    st.text_input(
        "Número do certificado",
        certificacao.numero_certificado or "-",
        disabled=True,
    )

    st.text_input(
        "Status",
        STATUS_LABELS[certificacao.status],
        disabled=True,
    )

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, id_certificacao)
        st.rerun()


@st.dialog("Editar certificação do lote", width="large")
def _edit_dialog(scope: str, id_certificacao: int) -> None:
    try:
        certificacao = client.get_certificacao(id_certificacao)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_certificacao)
            st.rerun()

        return

    dt_emissao = st.date_input(
        "Data de emissão",
        value=certificacao.dt_emissao,
    )

    dt_validade = st.date_input(
        "Data de validade",
        value=certificacao.dt_validade,
    )

    numero_certificado = st.text_input(
        "Número do certificado",
        value=certificacao.numero_certificado or "",
    )

    status = st.selectbox(
        "Status",
        options=list(StatusCertificacao),
        index=list(StatusCertificacao).index(certificacao.status),
        format_func=lambda s: STATUS_LABELS[s],
    )

    col1, col2 = st.columns(2)

    with col1:
        salvar = st.button("Salvar", use_container_width=True)

    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, id_certificacao)
        st.rerun()

    if not salvar:
        return

    try:
        payload = CertificacaoLoteUpdateSchema(
            dt_emissao=dt_emissao,
            dt_validade=dt_validade,
            numero_certificado=numero_certificado.strip() or None,
            status=status,
        )

        client.update_certificacao(id_certificacao, payload)

    except (EstoqueApiError, ValidationError) as exc:
        message = exc.user_message if isinstance(exc, EstoqueApiError) else str(exc)
        st.error(message)

        if isinstance(exc, EstoqueApiError) and st.button("Fechar"):
            clear_dialog_state(scope, id_certificacao)
            st.rerun()

        return

    st.toast("Certificação atualizada com sucesso.")
    clear_dialog_state(scope, id_certificacao)
    st.rerun()


@st.dialog("Excluir certificação")
def _delete_dialog(scope: str, id_certificacao: int) -> None:
    try:
        certificacao = client.get_certificacao(id_certificacao)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_certificacao)
            st.rerun()

        return

    st.warning(
        f"Deseja realmente remover a certificação "
        f"**{certificacao.certificacao_nome or '-'}** "
        f"do lote **{certificacao.lote_codigo or '-'}**?\n\n"
        "Essa ação não poderá ser desfeita."
    )
    
    col1, col2 = st.columns(2)

    with col1:
        excluir = st.button("Excluir", use_container_width=True)

    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, id_certificacao)
        st.rerun()

    if not excluir:
        return

    try:
        client.delete_certificacao(id_certificacao)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope, id_certificacao)
            st.rerun()

        return

    st.toast("Certificação excluída com sucesso.")
    clear_dialog_state(scope, id_certificacao)
    st.rerun()