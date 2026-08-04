"""Diálogos de recebimentos."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import streamlit as st

from app.financeiro.schemas import (
    RecebimentoCreateSchema,
    RecebimentoUpdateSchema,
)

from components.financeiro.dialog_state import (
    clear_dialog_state,
    get_dialog,
)

from components.financeiro.formatters import (
    conta_receber_label,
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



@st.dialog("Novo recebimento", width="large")
def _create_dialog(scope: str) -> None:
    try:
        contas = client.list_conta_receber_options()
        formas = client.list_forma_pagamento_options()

    except FinanceiroApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return


    if not contas:
        st.info("Nenhuma conta a receber disponível.")
        return


    conta = st.selectbox(
        "Conta a receber",
        contas,
        format_func=conta_receber_label,
    )


    saldo = conta.saldo or Decimal("0.00")


    st.info(
        f"Saldo disponível: R$ {format_money(float(saldo))}"
    )


    valor = st.number_input(
        "Valor recebido",
        min_value=0.0,
        value=float(saldo),
        step=0.01,
    )


    data_recebimento = st.date_input(
        "Data do recebimento",
        value=date.today(),
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


    payload = RecebimentoCreateSchema(
        id_conta_receber=conta.id_conta_receber,
        valor_recebido=Decimal(str(valor)),
        data_recebimento=data_recebimento,
        forma_pagamento=forma.valor,
    )


    try:
        client.create_recebimento(payload)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return


    st.toast("Recebimento cadastrado com sucesso.")

    clear_dialog_state(scope)
    st.rerun()



@st.dialog("Recebimento")
def _view_dialog(
    scope: str,
    entity_id: int | None,
) -> None:

    if entity_id is None:
        return


    try:
        recebimento = client.get_recebimento(entity_id)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return


    st.write(
        f"**Conta a receber:** "
        f"{recebimento.id_conta_receber}"
    )


    st.write(
        f"**Valor recebido:** "
        f"R$ {format_money(float(recebimento.valor_recebido))}"
    )


    st.write(
        f"**Data recebimento:** "
        f"{recebimento.data_recebimento}"
    )


    st.write(
        f"**Forma de pagamento:** "
        f"{recebimento.forma_pagamento or '-'}"
    )


    st.write(
        f"**Saldo restante:** "
        f"R$ {format_money(float(recebimento.saldo or 0))}"
    )


    if st.button("Fechar"):
        clear_dialog_state(scope)
        st.rerun()



@st.dialog("Editar recebimento")
def _edit_dialog(
    scope: str,
    entity_id: int | None,
) -> None:

    if entity_id is None:
        return


    try:
        recebimento = client.get_recebimento(entity_id)
        formas = client.list_forma_pagamento_options()

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return


    data_recebimento = st.date_input(
        "Data do recebimento",
        value=recebimento.data_recebimento,
    )


    forma_atual = recebimento.forma_pagamento

    valores_forma = [
        forma.valor
        for forma in formas
    ]


    index = (
        valores_forma.index(forma_atual)
        if forma_atual in valores_forma
        else 0
    )


    forma_pagamento = st.selectbox(
        "Forma de pagamento",
        formas,
        index=index,
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


    payload = RecebimentoUpdateSchema(
        data_recebimento=data_recebimento,
        forma_pagamento=forma_pagamento.valor,
    )


    try:
        client.update_recebimento(
            entity_id,
            payload,
        )

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return


    st.toast("Recebimento atualizado.")

    clear_dialog_state(scope)
    st.rerun()



@st.dialog("Excluir recebimento")
def _delete_dialog(
    scope: str,
    entity_id: int | None,
) -> None:

    if entity_id is None:
        return


    st.warning(
        "Deseja realmente excluir este recebimento?"
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
        client.delete_recebimento(entity_id)

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return


    st.toast("Recebimento excluído.")

    clear_dialog_state(scope)
    st.rerun()