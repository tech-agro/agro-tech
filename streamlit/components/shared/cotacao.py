"""Widget de cotacao de commodities (AgroDoc/CEPEA) reutilizavel entre
Inteligencia e Comercial."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from components.shared.charts import trend_chart
from services.inteligencia_client import InteligenciaApiError, InteligenciaClient

_UFS = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
)
_INDICADOR_PREFIXOS = ("Boi Gordo", "Vaca Gorda", "Soja", "Milho", "Bezerro")


def _client() -> InteligenciaClient:
    return InteligenciaClient()


def render_uf_input(*, key_prefix: str) -> str | None:
    """Selectbox de UF opcional — usado para trazer o preco fisico regional do boi."""
    opcoes = ("Nenhuma (so precos nacionais)",) + _UFS
    escolha = st.selectbox(
        "UF (opcional, preco regional do boi)",
        opcoes,
        key=f"{key_prefix}_uf",
    )
    return None if escolha == opcoes[0] else escolha


def render_cotacao_atual(*, uf: str | None = None) -> None:
    """Card com a leitura ao vivo (sem persistir) das cotacoes CEPEA/AgroDoc."""
    try:
        cotacoes = _client().get_cotacao_atual(uf=uf)
    except InteligenciaApiError as exc:
        st.warning(f"Nao foi possivel consultar a cotacao agora: {exc.user_message}")
        return

    if not cotacoes:
        st.info("Nenhuma cotacao disponivel no momento.")
        return

    colunas = st.columns(min(len(cotacoes), 3))
    for i, cotacao in enumerate(cotacoes):
        with colunas[i % len(colunas)]:
            st.metric(
                cotacao.product,
                f"R$ {cotacao.price:,.2f}",
                help=cotacao.unit,
            )

    primeira = cotacoes[0]
    rodape = []
    if primeira.source:
        rodape.append(f"Fonte: {primeira.source}")
    if primeira.updated_at:
        rodape.append(f"Atualizado: {primeira.updated_at}")
    if rodape:
        st.caption(" · ".join(rodape))


def render_cotacao_trend(*, dias: int = 60, height: int = 220) -> None:
    """Grafico de historico de cotacoes a partir de sincronizacoes salvas."""
    try:
        medicoes = _client().list_medicoes(
            data_inicio=date.today() - timedelta(days=dias),
            data_fim=date.today(),
        )
    except InteligenciaApiError:
        medicoes = []

    linhas = [
        {
            "data": m.data_referencia,
            "valor": float(m.valor),
            "indicador": m.indicador_nome,
        }
        for m in medicoes
        if m.indicador_nome is not None
        and m.indicador_nome.startswith(_INDICADOR_PREFIXOS)
        and m.valor is not None
        and m.data_referencia is not None
    ]
    if not linhas:
        st.caption(
            "Sem historico de cotacao ainda. Clique em 'Sincronizar' para registrar a "
            "primeira leitura."
        )
        return

    df = pd.DataFrame(linhas).groupby(["data", "indicador"], as_index=False)["valor"].mean()
    trend_chart(df, x="data", y="valor", color_field="indicador", y_title="R$", height=height)
