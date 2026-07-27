"""Diálogos de contas a receber."""

from __future__ import annotations

from decimal import Decimal

import streamlit as st

from app.financeiro.schemas import (
    ContaReceberCreateSchema,
    ContaReceberUpdateSchema,
)
from components.financeiro.dialog_state import (
    clear_dialog_state,
    get_dialog,
)
from components.financeiro.formatters import (
    venda_label,
)
from components.shared.formatters import format_money

from services.financeiro_client import (
    FinanceiroApiError,
    FinanceiroClient,
)


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


@st.dialog("Nova conta a receber", width="large")
def _create_dialog(scope: str) -> None:
    try:
        vendas = client.list_venda_options()

    except FinanceiroApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return


    if not vendas:
        st.info("Nenhuma venda disponível.")
        return


    venda = st.selectbox(
        "Venda",
        vendas,
        format_func=venda_label,
    )

    valor = venda.valor_total or Decimal("0")

    st.info(
        f"Valor: R$ {format_money(float(valor))}"
    )


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


    payload = ContaReceberCreateSchema(
        id_venda=venda.id_venda,
        valor=valor,
        vencimento=vencimento,
    )


    try:
        client.create_conta_receber(payload)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return


    st.toast("Conta a receber cadastrada com sucesso.")

    clear_dialog_state(scope)
    st.rerun()



@st.dialog("Conta a receber")
def _view_dialog(
    scope: str,
    entity_id: int | None,
) -> None:

    if entity_id is None:
        return


    try:
        conta = client.get_conta_receber(entity_id)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return


    st.write(
        f"**Venda:** {conta.id_venda}"
    )

    st.write(
        f"**Valor:** R$ {format_money(float(conta.valor))}"
    )

    st.write(
        f"**Valor recebido:** "
        f"R$ {format_money(float(conta.valor_recebido))}"
    )

    st.write(
        f"**Saldo:** "
        f"R$ {format_money(float(conta.saldo))}"
    )

    st.write(
        f"**Vencimento:** {conta.vencimento}"
    )

    st.write(
        f"**Status:** {conta.status.value}"
    )


    if st.button("Fechar"):
        clear_dialog_state(scope)
        st.rerun()



@st.dialog("Editar conta a receber")
def _edit_dialog(
    scope: str,
    entity_id: int | None,
) -> None:

    if entity_id is None:
        return


    try:
        conta = client.get_conta_receber(entity_id)

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


    payload = ContaReceberUpdateSchema(
        vencimento=vencimento,
        status=status,
    )


    try:
        client.update_conta_receber(
            entity_id,
            payload,
        )

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return


    st.toast("Conta a receber atualizada.")

    clear_dialog_state(scope)
    st.rerun()



@st.dialog("Excluir conta a receber")
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
        client.delete_conta_receber(entity_id)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return


    st.toast("Conta a receber excluída.")

    clear_dialog_state(scope)
    st.rerun()