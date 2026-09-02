"""BI dashboard for the logistics module."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from components.bi import charts
from components.bi.filters import render_filter_bar
from components.bi.widgets import delta_label, download_csv, fmt_brl, fmt_int
from components.logistica.formatters import OPERATION_STATUS_LABELS
from components.logistica.operation_tables import OPERATION_STATUS_OPTIONS, OPERATION_STATUS_TONE
from components.shared.palette import badge_column, badge_value
from components.shared.screens import setup_page, toast_error
from services import producao_client as producao_api
from services.estoque_client import EstoqueApiError, EstoqueClient
from services.logistica_client import LogisticsApiError, LogisticsClient

_FORA_SAFRA = "Fora de safra"


@st.cache_data(ttl=60)
def _list_operations_cached() -> list:
    return _client().list_operations()


@st.cache_data(ttl=60)
def _list_loads_cached() -> list:
    return _client().list_all_loads()


@st.cache_data(ttl=60)
def _load_safras_cached() -> list[dict]:
    try:
        return producao_api.listar("/safras")
    except Exception:
        st.warning("Nao foi possivel carregar as safras para o filtro.")
        return []


@st.cache_data(ttl=60)
def _list_lotes_cached() -> list:
    try:
        return EstoqueClient().list_lotes(limit=1000)
    except EstoqueApiError:
        return []


@st.cache_data(ttl=60)
def _fetch_dispatch(operation_id: int, load_id: int):
    return _client().get_dispatch(operation_id, load_id)


def _client() -> LogisticsClient:
    return LogisticsClient()


def _as_date(value) -> date | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _safra_label(item: dict) -> str:
    return f"{item.get('nome', 'Safra')} ({item.get('ano', '')})"


@st.cache_data(ttl=60)
def _load_production_links() -> tuple[list[dict], list[dict], list[dict]]:
    try:
        return (
            producao_api.listar("/plantios"),
            producao_api.listar("/ordens-producao"),
            producao_api.listar("/colheitas"),
        )
    except Exception:
        st.warning("Nao foi possivel vincular lotes a safras.")
        return [], [], []


def _load_lot_safra_map(lotes: list) -> tuple[list[dict], dict[int, int]]:
    safras = _load_safras_cached()
    if not safras:
        return [], {}

    plantios, ordens, colheitas = _load_production_links()
    if not plantios and not ordens and not colheitas:
        return safras, {}

    ordem_safra = {int(o["id_ordem"]): int(o["id_safra"]) for o in ordens}
    plantio_safra = {
        int(p["id_plantio"]): ordem_safra.get(int(p["id_ordem"]))
        for p in plantios
        if int(p["id_ordem"]) in ordem_safra
    }
    colheita_safra = {
        int(c["id_colheita"]): plantio_safra.get(int(c["id_plantio"]))
        for c in colheitas
        if plantio_safra.get(int(c["id_plantio"])) is not None
    }

    lot_to_safra: dict[int, int] = {}
    for lote in lotes:
        if lote.id_colheita is None:
            continue
        id_safra = colheita_safra.get(int(lote.id_colheita))
        if id_safra is not None:
            lot_to_safra[int(lote.id_lote)] = id_safra
    return safras, lot_to_safra


def _operation_safra(loads: list, lot_to_safra: dict[int, int], safras: dict[int, str]) -> str:
    labels = {
        safras.get(id_safra, _FORA_SAFRA)
        for load in loads
        for id_safra in [lot_to_safra.get(int(load.id_lote))]
        if id_safra is not None
    }
    if not labels:
        return _FORA_SAFRA
    if len(labels) == 1:
        return next(iter(labels))
    return sorted(labels)[0]


def _slice_period(df: pd.DataFrame, start: date | None, end: date | None) -> pd.DataFrame:
    if df.empty:
        return df
    if start is None and end is None:
        return df
    mask = df["Data"].notna()
    if start is not None:
        mask &= df["Data"] >= start
    if end is not None:
        mask &= df["Data"] <= end
    return df[mask]


def _previous_span(start: date, end: date) -> tuple[date, date]:
    length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    return prev_end - timedelta(days=length - 1), prev_end


def render() -> None:
    setup_page("Logistica", "Custo de frete e desempenho de entregas")

    try:
        operations = _list_operations_cached()
        loads = _list_loads_cached()
    except LogisticsApiError as exc:
        toast_error(exc)
        st.stop()

    lotes = _list_lotes_cached()

    safras, lot_to_safra = _load_lot_safra_map(lotes)
    safra_by_id = {int(item["id_safra"]): _safra_label(item) for item in safras}
    loads_by_op: dict[int, list] = defaultdict(list)
    for load in loads:
        loads_by_op[load.id_operacao].append(load)

    def _tempo_medio_operacao(operation_id: int, op_loads: list) -> float | None:
        duracoes: list[float] = []
        for load in op_loads:
            dispatch = _fetch_dispatch(operation_id, load.id_carga)
            if dispatch is None or dispatch.data_saida is None or dispatch.data_entrega is None:
                continue
            delta = dispatch.data_entrega - dispatch.data_saida
            if delta.total_seconds() >= 0:
                duracoes.append(delta.total_seconds() / 3600.0)
        if not duracoes:
            return None
        return sum(duracoes) / len(duracoes)

    rows: list[dict] = []
    for operation in operations:
        op_loads = loads_by_op.get(operation.id_operacao, [])
        if not op_loads and operation.custo_previsto is None:
            continue

        safra = _operation_safra(op_loads, lot_to_safra, safra_by_id)
        data_ref = _as_date(operation.data_inicio) or _as_date(operation.data_fim)
        tempo_horas = _tempo_medio_operacao(operation.id_operacao, op_loads)

        rows.append(
            {
                "Operacao": operation.id_operacao,
                "Data": data_ref,
                "Safra": safra,
                "Custo frete": float(operation.custo_previsto or 0.0),
                "Tempo desp/entrega (h)": float(tempo_horas) if tempo_horas is not None else None,
                "Status": OPERATION_STATUS_LABELS.get(operation.status, operation.status.value if operation.status else None),
            }
        )

    filtros = render_filter_bar(
        prefix="bi_logistica",
        safra_options=[_safra_label(s) for s in safras] + [_FORA_SAFRA],
        product_options=[],
    )

    df_all = pd.DataFrame(rows)
    df = _slice_period(df_all, filtros.start, filtros.end)
    if filtros.safra:
        df = df[df["Safra"] == filtros.safra]

    prev_start, prev_end = _previous_span(filtros.start or date.today() - timedelta(days=89), filtros.end or date.today()) if filtros.start or filtros.end else (None, None)
    prev_df = (
        _slice_period(df_all, prev_start, prev_end)
        if prev_start is not None and prev_end is not None
        else pd.DataFrame(columns=df_all.columns)
    )
    if filtros.safra:
        prev_df = prev_df[prev_df["Safra"] == filtros.safra]

    total_frete = float(df["Custo frete"].sum()) if not df.empty else 0.0
    total_frete_prev = float(prev_df["Custo frete"].sum()) if not prev_df.empty else 0.0
    total_operacoes = int(df["Operacao"].nunique()) if not df.empty else 0
    total_operacoes_prev = int(prev_df["Operacao"].nunique()) if not prev_df.empty else 0
    prazo_medio = (
        float(df["Tempo desp/entrega (h)"].mean())
        if not df.empty and df["Tempo desp/entrega (h)"].notna().any()
        else 0.0
    )
    prazo_medio_prev = (
        float(prev_df["Tempo desp/entrega (h)"].mean())
        if not prev_df.empty and prev_df["Tempo desp/entrega (h)"].notna().any()
        else 0.0
    )

    with st.container(horizontal=True):
        st.metric(
            "Custo de frete",
            fmt_brl(total_frete),
            delta=delta_label(total_frete, total_frete_prev, formatter=fmt_brl),
            delta_color="inverse",
            border=True,
        )
        st.metric(
            "Custo médio por operação",
            fmt_brl(total_frete / total_operacoes) if total_operacoes else "R$ 0,00",
            delta=delta_label(
                total_frete / total_operacoes if total_operacoes else 0.0,
                total_frete_prev / total_operacoes_prev if total_operacoes_prev else 0.0,
                formatter=fmt_brl,
            ),
            delta_color="inverse",
            border=True,
        )
        st.metric(
            "Tempo médio entre despacho e entrega",
            f"{prazo_medio:.1f} h" if prazo_medio else "0.0 h",
            delta=delta_label(prazo_medio, prazo_medio_prev, formatter=lambda value: f"{value:.1f} h"),
            delta_color="inverse",
            border=True,
        )
        st.metric(
            "Operações",
            fmt_int(total_operacoes),
            delta=delta_label(total_operacoes, total_operacoes_prev, formatter=fmt_int),
            border=True,
        )
    col_chart, col_table = st.columns([1.1, 1.4])

    with col_chart:
        if df.empty:
            by_safra = pd.DataFrame(columns=["Safra", "Custo frete"])
        else:
            by_safra = df.groupby("Safra", as_index=False).agg({"Custo frete": "sum"})
            by_safra = by_safra.sort_values(by="Custo frete", ascending=False)
        if not by_safra.empty:
            st.subheader("Custo por safra")
            charts.bar_chart(by_safra, x="Safra", y="Custo frete", y_title="Custo de frete (R$)")
        else:
            st.info("Nenhuma operação encontrada para os filtros selecionados.")

    with col_table:
        st.subheader("Operações e indicadores")
        display_df = df.copy()
        if not display_df.empty:
            display_df = display_df[["Operacao", "Data", "Safra", "Custo frete", "Tempo desp/entrega (h)", "Status"]]
            # NaN in a NumberColumn renders as the literal text "None" in
            # this Streamlit build — format as text with an em dash instead.
            display_df["Tempo desp/entrega (h)"] = pd.to_numeric(
                display_df["Tempo desp/entrega (h)"], errors="coerce"
            ).map(lambda v: f"{v:.1f} h" if pd.notna(v) else "—")
            display_df["Status"] = display_df["Status"].apply(badge_value)
        st.dataframe(
            display_df,
            hide_index=True,
            column_config={
                "Operacao": st.column_config.TextColumn("Operação", pinned=True),
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Safra": st.column_config.TextColumn("Safra"),
                "Custo frete": st.column_config.NumberColumn("Custo de frete (R$)", format="localized"),
                "Tempo desp/entrega (h)": st.column_config.TextColumn("Tempo desp/entrega (h)", alignment="right"),
                "Status": badge_column("Status", OPERATION_STATUS_OPTIONS, OPERATION_STATUS_TONE, width="medium"),
            },
        )
        download_csv(
            df.rename(
                columns={
                    "Operacao": "operacao",
                    "Data": "data",
                    "Safra": "safra",
                    "Custo frete": "custo_frete",
                    "Tempo desp/entrega (h)": "tempo_despacho_entrega_horas",
                    "Status": "status",
                }
            ),
            filename="dashboard_logistica.csv",
            key="bi_logistica_csv",
        )
