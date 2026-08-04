"""Diálogos de fluxo de caixa."""

from __future__ import annotations

import streamlit as st

from components.financeiro.dialog_state import (
    clear_dialog_state,
    get_dialog,
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

    if kind == "view":
        _view_dialog(scope, entity_id)



@st.dialog("Movimentação do fluxo de caixa", width="large")
def _view_dialog(
    scope: str,
    entity_id: int | None,
) -> None:

    if entity_id is None:
        return


    # O endpoint de detalhe não existe no client.
    # Como fluxo é somente consulta por período/conta,
    # buscamos o lançamento através dos fluxos recentes.
    fluxo = None

    try:
        from datetime import date

        registros = client.list_fluxo_por_periodo(
            data_inicio=date(2000, 1, 1),
            data_fim=date.today(),
            limit=500,
        )

        fluxo = next(
            (
                item
                for item in registros
                if item.id_fluxo == entity_id
            ),
            None,
        )

    except FinanceiroApiError as exc:
        st.error(exc.user_message)
        return


    if fluxo is None:
        st.error("Movimentação de fluxo de caixa não encontrada.")

        if st.button(
            "Fechar",
            use_container_width=True,
        ):
            clear_dialog_state(scope)
            st.rerun()

        return


    st.write(
        f"**Tipo:** {fluxo.tipo or '-'}"
    )

    st.write(
        f"**Valor:** "
        f"R$ {format_money(float(fluxo.valor))}"
    )

    st.write(
        f"**Data movimento:** "
        f"{fluxo.data_movimento or '-'}"
    )

    st.write(
        f"**Origem:** "
        f"{fluxo.origem or '-'}"
    )

    st.write(
        f"**Descrição:** "
        f"{fluxo.descricao_origem or '-'}"
    )


    st.divider()


    if fluxo.id_conta_pagar is not None:
        st.write(
            f"**Conta a pagar:** {fluxo.id_conta_pagar}"
        )

    if fluxo.id_conta_receber is not None:
        st.write(
            f"**Conta a receber:** {fluxo.id_conta_receber}"
        )

    if fluxo.id_pagamento is not None:
        st.write(
            f"**Pagamento:** {fluxo.id_pagamento}"
        )

    if fluxo.id_recebimento is not None:
        st.write(
            f"**Recebimento:** {fluxo.id_recebimento}"
        )


    if st.button(
        "Fechar",
        use_container_width=True,
    ):
        clear_dialog_state(scope)
        st.rerun()