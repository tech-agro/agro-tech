"""Home dashboard: resumo financeiro e widget de clima (Open-Meteo)."""

from __future__ import annotations

import streamlit as st

from components.financeiro import intelligence as financeiro_intel
from components.shared import clima
from services.financeiro_client import FinanceiroApiError, FinanceiroClient


def _financeiro_client() -> FinanceiroClient:
    return FinanceiroClient()


def _render_financeiro_resumo() -> None:
    st.subheader("Financeiro")
    try:
        contas_pagar = _financeiro_client().list_contas_pagar(limit=500)
        contas_receber = _financeiro_client().list_contas_receber(limit=500)
    except FinanceiroApiError as exc:
        st.warning(f"Nao foi possivel carregar o resumo financeiro: {exc.user_message}")
        return

    financeiro_intel.render_kpis(contas_pagar, contas_receber)


def _render_clima() -> None:
    st.subheader("Clima")
    latitude, longitude = clima.render_localizacao(key_prefix="home_clima")
    clima.render_clima_atual(latitude=latitude, longitude=longitude)
    clima.render_clima_trend()


def render_dashboard() -> None:
    _render_financeiro_resumo()
    st.divider()
    _render_clima()
