"""Widget de clima (Open-Meteo) reutilizavel entre Home e Inteligencia."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from components.shared.charts import trend_chart
from services.inteligencia_client import InteligenciaApiError, InteligenciaClient

_INDICADORES_CLIMA = {"Temperatura", "Umidade relativa", "Precipitacao"}

DEFAULT_LAT = -8.0578
DEFAULT_LON = -34.8829


def _client() -> InteligenciaClient:
    return InteligenciaClient()


def render_localizacao(*, key_prefix: str) -> tuple[float, float]:
    col_lat, col_lon = st.columns(2)
    with col_lat:
        latitude = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=DEFAULT_LAT,
            format="%.4f",
            key=f"{key_prefix}_lat",
        )
    with col_lon:
        longitude = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=DEFAULT_LON,
            format="%.4f",
            key=f"{key_prefix}_lon",
        )
    return latitude, longitude


def render_clima_atual(*, latitude: float, longitude: float) -> None:
    """Card com a leitura ao vivo (sem persistir) do clima na coordenada."""
    try:
        atual = _client().get_clima_atual(latitude=latitude, longitude=longitude)
    except InteligenciaApiError as exc:
        st.warning(f"Nao foi possivel consultar o clima agora: {exc.user_message}")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Temperatura",
        f"{atual.temperature_c:.1f} °C" if atual.temperature_c is not None else "—",
    )
    c2.metric(
        "Umidade",
        f"{atual.humidity_pct:.0f}%" if atual.humidity_pct is not None else "—",
    )
    c3.metric(
        "Precipitacao",
        f"{atual.precipitation_mm:.1f} mm" if atual.precipitation_mm is not None else "—",
    )


def render_clima_trend(*, dias: int = 30, height: int = 220) -> None:
    """Grafico de historico (Temperatura/Umidade/Precipitacao) a partir de sincronizacoes salvas."""
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
        if m.indicador_nome in _INDICADORES_CLIMA
        and m.valor is not None
        and m.data_referencia is not None
    ]
    if not linhas:
        st.caption(
            "Sem historico de clima ainda. Clique em 'Sincronizar' para registrar a "
            "primeira leitura."
        )
        return

    df = pd.DataFrame(linhas).groupby(["data", "indicador"], as_index=False)["valor"].mean()
    trend_chart(df, x="data", y="valor", color_field="indicador", y_title="Valor", height=height)
