"""Financeiro — contas, pagamentos, recebimentos e fluxo de caixa."""

from __future__ import annotations

from pathlib import Path
import sys
from datetime import date, timedelta

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st


from components.financeiro import (
    conta_pagar_dialogs,
    pagamento_dialogs,
    conta_receber_dialogs,
    recebimento_dialogs,
)

from components.financeiro.dialog_state import open_dialog

from components.financeiro.conta_pagar_tables import contas_pagar_df
from components.financeiro.pagamento_tables import pagamentos_df
from components.financeiro.conta_receber_tables import contas_receber_dataframe
from components.financeiro.recebimento_tables import recebimentos_df
from components.financeiro.fluxo_caixa_tables import fluxo_caixa_df
from components.financeiro import intelligence

from components.shared.screens import (
    setup_page,
    crud_toolbar,
    data_table,
    filter_dataframe,
    row_actions,
    toast_error,
)

from services.financeiro_client import (
    FinanceiroApiError,
    FinanceiroClient,
)


setup_page(
    "Financeiro",
    "Controle de contas a pagar, receber, pagamentos, recebimentos e fluxo de caixa.",
)


def _client() -> FinanceiroClient:
    return FinanceiroClient()


(
    tab_visao_geral,
    tab_vencimentos,
    tab_pagar,
    tab_pagamentos,
    tab_receber,
    tab_recebimentos,
    tab_fluxo,
) = st.tabs(
    [
        "Visão geral",
        "Vencimentos",
        "Contas a pagar",
        "Pagamentos",
        "Contas a receber",
        "Recebimentos",
        "Fluxo de caixa",
    ]
)


# ============================================================
# VISAO GERAL (inteligencia financeira)
# ============================================================

with tab_visao_geral:
    try:
        _contas_pagar = _client().list_contas_pagar(limit=500)
        _contas_receber = _client().list_contas_receber(limit=500)
        _fluxo_90d = _client().list_fluxo_por_periodo(
            data_inicio=date.today() - timedelta(days=90),
            data_fim=date.today(),
            limit=500,
        )
    except FinanceiroApiError as exc:
        toast_error(exc)
        st.stop()

    intelligence.render_kpis(_contas_pagar, _contas_receber)
    st.caption("Entradas e saídas de caixa — últimos 90 dias")
    intelligence.render_fluxo_chart(_fluxo_90d)


# ============================================================
# VENCIMENTOS (aging)
# ============================================================

with tab_vencimentos:
    try:
        _contas_pagar_v = _client().list_contas_pagar(limit=500)
        _contas_receber_v = _client().list_contas_receber(limit=500)
    except FinanceiroApiError as exc:
        toast_error(exc)
        st.stop()

    intelligence.render_aging_chart(_contas_pagar_v, _contas_receber_v)
    st.caption("Contas em atraso")
    intelligence.render_criticas_table(_contas_pagar_v, _contas_receber_v)


# ============================================================
# CONTAS A PAGAR
# ============================================================

with tab_pagar:

    try:
        contas = _client().list_contas_pagar(limit=500)

    except FinanceiroApiError as exc:
        toast_error(exc)
        st.stop()


    query, new_clicked = crud_toolbar(
        key="contas_pagar",
        filter_placeholder="Filtrar contas a pagar...",
        new_label="Nova conta",
    )


    if new_clicked:
        open_dialog(
            "contas_pagar",
            "create",
        )


    df = filter_dataframe(
        contas_pagar_df(contas),
        query,
    )


    selected = data_table(
        df,
        key="contas_pagar_grid",
    )


    action = row_actions(
        key="contas_pagar",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )


    if action == "view" and selected:
        open_dialog(
            "contas_pagar",
            "view",
            int(selected[0]["ID"]),
        )

    elif action == "edit" and selected:
        open_dialog(
            "contas_pagar",
            "edit",
            int(selected[0]["ID"]),
        )

    elif action == "delete" and selected:
        open_dialog(
            "contas_pagar",
            "delete",
            int(selected[0]["ID"]),
        )


    conta_pagar_dialogs.render(
        "contas_pagar"
    )


# ============================================================
# PAGAMENTOS
# ============================================================

with tab_pagamentos:

    try:
        pagamentos = _client().list_pagamentos(
            limit=500
        )

    except FinanceiroApiError as exc:
        toast_error(exc)
        st.stop()


    query, new_clicked = crud_toolbar(
        key="pagamentos",
        filter_placeholder="Filtrar pagamentos...",
        new_label="Novo pagamento",
    )


    if new_clicked:
        open_dialog(
            "pagamentos",
            "create",
        )


    df = filter_dataframe(
        pagamentos_df(pagamentos),
        query,
    )


    selected = data_table(
        df,
        key="pagamentos_grid",
    )


    action = row_actions(
        key="pagamentos",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )


    if action == "view" and selected:
        open_dialog(
            "pagamentos",
            "view",
            int(selected[0]["ID"]),
        )

    elif action == "edit" and selected:
        open_dialog(
            "pagamentos",
            "edit",
            int(selected[0]["ID"]),
        )

    elif action == "delete" and selected:
        open_dialog(
            "pagamentos",
            "delete",
            int(selected[0]["ID"]),
        )


    pagamento_dialogs.render(
        "pagamentos"
    )


# ============================================================
# CONTAS A RECEBER
# ============================================================

with tab_receber:

    try:
        contas = _client().list_contas_receber(
            limit=500
        )

    except FinanceiroApiError as exc:
        toast_error(exc)
        st.stop()


    query, new_clicked = crud_toolbar(
        key="contas_receber",
        filter_placeholder="Filtrar contas a receber...",
        new_label="Nova conta",
    )


    if new_clicked:
        open_dialog(
            "contas_receber",
            "create",
        )


    df = filter_dataframe(
        contas_receber_dataframe(contas),
        query,
    )


    selected = data_table(
        df,
        key="contas_receber_grid",
    )


    action = row_actions(
        key="contas_receber",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )


    if action == "view" and selected:
        open_dialog(
            "contas_receber",
            "view",
            int(selected[0]["ID"]),
        )

    elif action == "edit" and selected:
        open_dialog(
            "contas_receber",
            "edit",
            int(selected[0]["ID"]),
        )

    elif action == "delete" and selected:
        open_dialog(
            "contas_receber",
            "delete",
            int(selected[0]["ID"]),
        )


    conta_receber_dialogs.render(
        "contas_receber"
    )


# ============================================================
# RECEBIMENTOS
# ============================================================

with tab_recebimentos:

    try:
        recebimentos = _client().list_recebimentos(
            limit=500
        )

    except FinanceiroApiError as exc:
        toast_error(exc)
        st.stop()


    query, new_clicked = crud_toolbar(
        key="recebimentos",
        filter_placeholder="Filtrar recebimentos...",
        new_label="Novo recebimento",
    )


    if new_clicked:
        open_dialog(
            "recebimentos",
            "create",
        )


    df = filter_dataframe(
        recebimentos_df(recebimentos),
        query,
    )


    selected = data_table(
        df,
        key="recebimentos_grid",
    )


    action = row_actions(
        key="recebimentos",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )


    if action == "view" and selected:
        open_dialog(
            "recebimentos",
            "view",
            int(selected[0]["ID"]),
        )

    elif action == "edit" and selected:
        open_dialog(
            "recebimentos",
            "edit",
            int(selected[0]["ID"]),
        )

    elif action == "delete" and selected:
        open_dialog(
            "recebimentos",
            "delete",
            int(selected[0]["ID"]),
        )


    recebimento_dialogs.render(
        "recebimentos"
    )


# ============================================================
# FLUXO DE CAIXA
# ============================================================

with tab_fluxo:

    col1, col2 = st.columns(2)

    with col1:
        data_inicio = st.date_input(
            "Data inicial",
            value=date.today() - timedelta(days=30),
        )

    with col2:
        data_fim = st.date_input(
            "Data final",
            value=date.today(),
        )


    if data_inicio > data_fim:
        st.warning(
            "A data inicial deve ser menor que a data final."
        )
        st.stop()


    try:
        fluxo = _client().list_fluxo_por_periodo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=500,
        )

    except FinanceiroApiError as exc:
        toast_error(exc)
        st.stop()


    st.dataframe(
        fluxo_caixa_df(fluxo),
        use_container_width=True,
        hide_index=True,
    )