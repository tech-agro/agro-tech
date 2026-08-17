"""BI wrapper for financeiro intelligence: KPIs, fluxo de caixa e aging (centralized in Inteligência).

This component reuses the existing components.financeiro.intelligence helpers and
exposes a compact render() that fetches data and displays the KPIs, fluxo chart and
aging chart for the Intelligence area.
"""

from __future__ import annotations

from datetime import date, timedelta
import logging

import streamlit as st

from components.financeiro import intelligence as fin_intel
from components.bi.filters import render_filter_bar
from services.financeiro_client import FinanceiroApiError, FinanceiroClient


@st.cache_data(ttl=60)
def _list_contas_pagar_cached(limit: int = 500):
    return FinanceiroClient().list_contas_pagar(limit=limit)


@st.cache_data(ttl=60)
def _list_contas_receber_cached(limit: int = 500):
    return FinanceiroClient().list_contas_receber(limit=limit)


@st.cache_data(ttl=60)
def _list_fluxo_periodo_cached(start: date, end: date, limit: int = 500):
    return FinanceiroClient().list_fluxo_por_periodo(data_inicio=start, data_fim=end, limit=limit)


def render(*, lookback_days: int = 90) -> None:
    """Render the Financeiro intelligence overview used in Inteligência/BI.

    - lookback_days: number of days to include in the fluxo de caixa chart (default 90)
    """
    logger = logging.getLogger(__name__)

    # Render filter bar so user can choose period; fallback to last `lookback_days` if none chosen
    filtros = render_filter_bar(prefix="bi_financeiro", safra_options=[], product_options=[])
    start = filtros.start or (date.today() - timedelta(days=lookback_days))
    end = filtros.end or date.today()

    try:
        contas_pagar = _list_contas_pagar_cached()
        contas_receber = _list_contas_receber_cached()
        fluxo = _list_fluxo_periodo_cached(start, end)
    except FinanceiroApiError as exc:
        logger.exception("Erro na API de financeiro")
        st.error(exc.user_message)
        return
    except Exception:
        logger.exception("Erro inesperado ao carregar dados financeiros")
        st.error("Falha ao carregar dados financeiros. Entre em contato com o suporte.")
        return

    st.header("Inteligência Financeira")
    st.caption("KPIs e principais riscos financeiros")

    fin_intel.render_kpis(contas_pagar, contas_receber)
    st.divider()

    st.subheader("Fluxo de caixa")
    st.caption(f"Entradas e saídas de caixa — {start} até {end}")
    fin_intel.render_fluxo_chart(fluxo)

    st.divider()
    st.subheader("Aging / Vencimentos")
    fin_intel.render_aging_chart(contas_pagar, contas_receber)

    st.divider()
    st.subheader("Contas críticas")
    fin_intel.render_criticas_table(contas_pagar, contas_receber)
