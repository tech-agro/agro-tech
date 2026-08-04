"""Diálogos de contas a pagar."""

from __future__ import annotations

from decimal import Decimal

import streamlit as st

from app.financeiro.schemas import (
    ContaPagarCreateSchema,
    ContaPagarUpdateSchema,
)
from components.financeiro.dialog_state import (
    clear_dialog_state,
    get_dialog,
)
from components.financeiro.formatters import (
    aplicacao_label,
    compra_label,
    despesa_logistica_label,
    manutencao_label,
)
from services.financeiro_client import (
    FinanceiroApiError,
    FinanceiroClient,
)
from components.shared.formatters import format_money

client = FinanceiroClient()


def render(scope: str) -> None:
    """Renderiza o diálogo aberto."""

    dialog = get_dialog(scope)

    if dialog is None:
        return

    kind, entity_id = dialog

    if kind == "create":
        _create_dialog(scope)

    elif kind == "view":
        _view_dialog(scope, entity_id)

    elif kind == "edit":
        _edit_dialog(scope, entity_id)

    elif kind == "delete":
        _delete_dialog(scope, entity_id)


@st.dialog("Nova conta a pagar", width="large")
def _create_dialog(scope: str) -> None:
    try:
        compras = client.list_compra_options()
        manutencoes = client.list_manutencao_options()
        despesas = client.list_despesa_logistica_options()
        aplicacoes = client.list_aplicacao_options()

    except FinanceiroApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    origem = st.radio(
        "Origem",
        (
            "Compra",
            "Manutenção",
            "Despesa logística",
            "Aplicação fitossanitária",
        ),
    )

    id_compra = None
    id_manutencao = None
    id_despesa = None
    id_aplicacao = None
    valor = Decimal("0")

    if origem == "Compra":
        if not compras:
            st.info("Nenhuma compra disponível.")
            return

        compra = st.selectbox(
            "Compra",
            compras,
            format_func=compra_label,
        )
        id_compra = compra.id_compra
        valor = compra.valor_total or Decimal("0")

    elif origem == "Manutenção":
        if not manutencoes:
            st.info("Nenhuma manutenção disponível.")
            return

        manutencao = st.selectbox(
            "Manutenção",
            manutencoes,
            format_func=manutencao_label,
        )
        id_manutencao = manutencao.id_manutencao
        valor = manutencao.custo or Decimal("0")

    elif origem == "Despesa logística":
        if not despesas:
            st.info("Nenhuma despesa logística disponível.")
            return

        despesa = st.selectbox(
            "Despesa logística",
            despesas,
            format_func=despesa_logistica_label,
        )
        id_despesa = despesa.id_despesa
        valor = despesa.valor

    else:
        if not aplicacoes:
            st.info("Nenhuma aplicação fitossanitária disponível.")
            return

        aplicacao = st.selectbox(
            "Aplicação",
            aplicacoes,
            format_func=aplicacao_label,
        )
        id_aplicacao = aplicacao.id_aplicacao
        valor = aplicacao.valor

    st.info(f"Valor: R$ {format_money(float(valor))}")

    vencimento = st.date_input(
        "Vencimento",
        value=None,
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
        clear_dialog_state(scope)
        st.rerun()

    if not salvar:
        return

    payload = ContaPagarCreateSchema(
        id_compra=id_compra,
        id_manutencao=id_manutencao,
        id_despesa_logistica=id_despesa,
        id_aplicacao=id_aplicacao,
        valor=valor,
        vencimento=vencimento,
    )

    try:
        client.create_conta_pagar(payload)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Conta cadastrada com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Conta a pagar")
def _view_dialog(
    scope: str,
    entity_id: int | None,
) -> None:
    if entity_id is None:
        return

    try:
        conta = client.get_conta_pagar(entity_id)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return

    st.write(f"**Origem:** {conta.origem}")
    st.write(f"**Valor:** {conta.valor}")
    st.write(f"**Vencimento:** {conta.vencimento}")
    st.write(f"**Status:** {conta.status.value}")

    if st.button("Fechar"):
        clear_dialog_state(scope)
        st.rerun()


@st.dialog("Editar conta a pagar")
def _edit_dialog(
    scope: str,
    entity_id: int | None,
) -> None:
    if entity_id is None:
        return

    try:
        conta = client.get_conta_pagar(entity_id)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return

    vencimento = st.date_input(
        "Vencimento",
        value=conta.vencimento,
    )

    status = st.selectbox(
        "Status",
        options=list(type(conta.status)),
        index=list(type(conta.status)).index(conta.status),
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
        clear_dialog_state(scope)
        st.rerun()

    if not salvar:
        return

    payload = ContaPagarUpdateSchema(
        vencimento=vencimento,
        status=status,
    )

    try:
        client.update_conta_pagar(entity_id, payload)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Conta atualizada.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Excluir conta a pagar")
def _delete_dialog(
    scope: str,
    entity_id: int | None,
) -> None:
    if entity_id is None:
        return

    st.warning(
        "Deseja realmente excluir esta conta?"
    )

    col1, col2 = st.columns(2)

    with col1:
        excluir = st.button(
            "Excluir",
            type="primary",
            use_container_width=True,
        )

    with col2:
        cancelar = st.button(
            "Cancelar",
            use_container_width=True,
        )

    if cancelar:
        clear_dialog_state(scope)
        st.rerun()

    if not excluir:
        return

    try:
        client.delete_conta_pagar(entity_id)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Conta excluída.")
    clear_dialog_state(scope)
    st.rerun()