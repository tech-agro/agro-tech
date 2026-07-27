"""Diálogos de pagamentos."""

from __future__ import annotations

from decimal import Decimal

import streamlit as st

from app.financeiro.schemas import (
    PagamentoCreateSchema,
    PagamentoUpdateSchema,
)
from components.financeiro.dialog_state import (
    clear_dialog_state,
    get_dialog,
)
from components.financeiro.formatters import (
    conta_pagar_label,
    forma_pagamento_label,
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


@st.dialog("Novo pagamento", width="large")
def _create_dialog(scope: str) -> None:
    try:
        contas = client.list_conta_pagar_options()
        formas = client.list_forma_pagamento_options()

    except FinanceiroApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    if not contas:
        st.info("Nenhuma conta disponível.")
        return

    conta = st.selectbox(
        "Conta a pagar",
        contas,
        format_func=conta_pagar_label,
    )

    saldo = conta.saldo or Decimal("0")

    st.info(f"Saldo pendente: R$ {format_money(float(saldo))}")

    valor_pago = st.number_input(
        "Valor pago",
        min_value=0.0,
        max_value=float(saldo),
        value=float(saldo),
        step=0.01,
    )

    data_pagamento = st.date_input(
        "Data do pagamento",
        value=None,
    )

    forma = st.selectbox(
        "Forma de pagamento",
        formas,
        format_func=forma_pagamento_label,
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

    payload = PagamentoCreateSchema(
        id_conta_pagar=conta.id_conta_pagar,
        valor_pago=Decimal(str(valor_pago)),
        data_pagamento=data_pagamento,
        forma_pagamento=forma.valor,
    )

    try:
        client.create_pagamento(payload)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Pagamento cadastrado com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Pagamento")
def _view_dialog(
    scope: str,
    entity_id: int | None,
) -> None:
    if entity_id is None:
        return

    try:
        pagamento = client.get_pagamento(entity_id)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return

    st.write(f"**Conta:** {pagamento.id_conta_pagar}")
    st.write(f"**Valor pago:** R$ {format_money(float(pagamento.valor_pago))}")
    st.write(f"**Data:** {pagamento.data_pagamento}")
    st.write(f"**Forma de pagamento:** {pagamento.forma_pagamento}")

    if pagamento.status is not None:
        st.write(f"**Status da conta:** {pagamento.status.value}")

    if pagamento.saldo is not None:
        st.write(
            f"**Saldo restante:** R$ {format_money(float(pagamento.saldo))}"
        )

    if st.button("Fechar"):
        clear_dialog_state(scope)
        st.rerun()


@st.dialog("Editar pagamento")
def _edit_dialog(
    scope: str,
    entity_id: int | None,
) -> None:
    if entity_id is None:
        return

    try:
        pagamento = client.get_pagamento(entity_id)
        formas = client.list_forma_pagamento_options()

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return

    data_pagamento = st.date_input(
        "Data do pagamento",
        value=pagamento.data_pagamento,
    )

    indice = 0

    for i, forma in enumerate(formas):
        if forma.valor == pagamento.forma_pagamento:
            indice = i
            break

    forma = st.selectbox(
        "Forma de pagamento",
        formas,
        index=indice,
        format_func=forma_pagamento_label,
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

    payload = PagamentoUpdateSchema(
        data_pagamento=data_pagamento,
        forma_pagamento=forma.valor,
    )

    try:
        client.update_pagamento(entity_id, payload)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Pagamento atualizado.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Excluir pagamento")
def _delete_dialog(
    scope: str,
    entity_id: int | None,
) -> None:
    if entity_id is None:
        return

    st.warning(
        "Deseja realmente excluir este pagamento?"
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
        client.delete_pagamento(entity_id)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Pagamento excluído.")
    clear_dialog_state(scope)
    st.rerun()