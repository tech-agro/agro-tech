"""BI dashboard: Manutenção — custos por máquina e perfil preventiva x corretiva.

Exibe custo total e por máquina, proporção preventiva vs corretiva, filtros por
máquina e período, e exportação CSV. Baseado no estilo de margem_dashboard.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from components.bi.filters import render_filter_bar
from components.bi.widgets import download_csv, fmt_brl
from components.bi.charts import bar_chart, donut_chart
from components.shared.screens import setup_page, toast_error
from components.shared.palette import badge_column, badge_value, semantic
from components.manutencao import lookups as manut_lookups
from services import manutencao_client as manutencao_api

_TIPO_COLOR = {"Preventiva": "green", "Corretiva": "orange"}


@st.cache_data(ttl=60)
def _list_maquinas_cached() -> list[dict]:
    try:
        return manutencao_api.list_maquinas()
    except Exception:
        return []


@st.cache_data(ttl=60)
def _list_preventivas_cached(id_maquina: int | None = None) -> list[dict]:
    try:
        if id_maquina is None:
            return manutencao_api.list_manutencoes_preventivas()
        return manutencao_api.list_manutencoes_preventivas(id_maquina=id_maquina)
    except Exception:
        return []


@st.cache_data(ttl=60)
def _list_corretivas_cached(id_maquina: int | None = None) -> list[dict]:
    try:
        if id_maquina is None:
            return manutencao_api.list_manutencoes_corretivas()
        return manutencao_api.list_manutencoes_corretivas(id_maquina=id_maquina)
    except Exception:
        return []


@st.cache_data(ttl=60)
def _list_ordens_cached(id_maquina: int | None = None) -> list[dict]:
    try:
        if id_maquina is None:
            return manutencao_api.list_ordens_servico()
        return manutencao_api.list_ordens_servico(id_maquina=id_maquina)
    except Exception:
        return []


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime().date()


def _build_rows(items: list[dict], tipo: str, start: date | None, end: date | None) -> list[dict]:
    rows: list[dict] = []
    for item in items:
        base = item.get("manutencao") or {}
        if base.get("status") != "CONCLUIDA":
            continue
        dt = _as_date(base.get("dt_inicio"))
        if start and dt and dt < start:
            continue
        if end and dt and dt > end:
            continue
        rows.append(
            {
                "Maquina": item.get("nome_maquina") or "—",
                "Data": dt,
                "Tipo": tipo,
                "Custo": float(base.get("custo") or 0.0),
                "ID": base.get("id_manutencao"),
            }
        )
    return rows


def render() -> None:
    setup_page("Manutenção — BI", "Custo e perfil de manutenção: preventiva x corretiva.")

    try:
        maquinas = _list_maquinas_cached()
    except Exception as exc:
        toast_error(exc)
        st.stop()

    # Filters area: machine selector first, then the compact period filter below (full width)
    col_left, _col = st.columns([3, 1])
    with col_left:
        id_maquina = manut_lookups.select_maquina(
            "Máquina",
            maquinas,
            key="bi_manut_maquina",
            permitir_todos=True,
        )

    # Render the shared compact filter bar *below* the machine selector so the period
    # appears under the machine select (same arrangement as other dashboards).
    filtros = render_filter_bar(prefix="bi_manut", safra_options=None, product_options=None)

    start, end = filtros.start, filtros.end

    # Load maintenance data
    try:
        preventivas = _list_preventivas_cached(id_maquina)
        corretivas = _list_corretivas_cached(id_maquina)
        ordens = _list_ordens_cached(id_maquina)
    except Exception as exc:
        toast_error(exc)
        st.stop()

    manut_rows = _build_rows(preventivas, "Preventiva", start, end) + _build_rows(corretivas, "Corretiva", start, end)

    df_man = pd.DataFrame(manut_rows)

    # Ensure Custo is numeric and NaNs are zeros to satisfy plotting and typing
    if not df_man.empty:
        df_man = df_man.copy()
        df_man["Custo"] = pd.to_numeric(df_man["Custo"].fillna(0.0), errors="coerce").fillna(0.0)
    else:
        df_man = df_man.copy()

    total_cost = float(df_man["Custo"].sum()) if not df_man.empty else 0.0
    preventive_cost = float(df_man[df_man["Tipo"] == "Preventiva"]["Custo"].sum()) if not df_man.empty else 0.0
    corrective_cost = float(df_man[df_man["Tipo"] == "Corretiva"]["Custo"].sum()) if not df_man.empty else 0.0

    # KPIs (IND-17 custo por máquina, IND-18 proporção preventiva x corretiva)
    denom = preventive_cost + corrective_cost
    preventiva_pct = (100 * preventive_cost / denom) if denom > 0 else None
    with st.container(horizontal=True):
        st.metric(
            "Custo total concluído",
            fmt_brl(total_cost),
            border=True,
        )
        st.metric(
            "Preventiva (R$)",
            fmt_brl(preventive_cost),
            border=True,
        )
        st.metric(
            "Corretiva (R$)",
            fmt_brl(corrective_cost),
            border=True,
        )
        st.metric(
            "Quota preventiva",
            f"{preventiva_pct:.0f}%" if preventiva_pct is not None else "—",
            help="IND-18 — quanto maior, melhor o perfil de manutenção (menos imprevistos).",
            border=True,
        )

    if df_man.empty:
        st.info("Nenhum registro de manutenção concluída encontrado para os filtros selecionados.")
        return

    # Cost per machine (ensure grouping result is a DataFrame)
    per_machine = (
        df_man.groupby("Maquina", as_index=False).agg({"Custo": "sum"}).sort_values(by="Custo", ascending=False)
    )

    col_custo, col_perfil = st.columns([3, 2])
    with col_custo:
        st.subheader("Custo por máquina")
        bar_chart(per_machine, x="Maquina", y="Custo", x_title="Máquina", y_title="Custo (R$)")
    with col_perfil:
        st.subheader("Preventiva x Corretiva")
        pie_df = df_man.groupby("Tipo", as_index=False).agg({"Custo": "sum"}).reset_index(drop=True)
        pie_df["Custo"] = pd.to_numeric(pie_df["Custo"].fillna(0.0), errors="coerce").fillna(0.0)
        donut_chart(
            pie_df,
            category="Tipo",
            value="Custo",
            color_map={"Preventiva": semantic("green"), "Corretiva": semantic("orange")},
        )

    st.subheader("Detalhamento de manutenções")
    display = df_man.copy()
    if "Custo" not in display.columns:
        display["Custo"] = 0.0
    display["Custo"] = pd.to_numeric(display["Custo"], errors="coerce").fillna(0.0)
    display["Tipo"] = display["Tipo"].apply(badge_value)
    st.dataframe(
        display.sort_values(["Data"], ascending=False),
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True),
            "Maquina": st.column_config.TextColumn("Máquina", pinned=True),
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "Tipo": badge_column("Tipo", ["Preventiva", "Corretiva"], _TIPO_COLOR, width="small"),
            "Custo": st.column_config.NumberColumn("Custo (R$)", format="localized"),
        },
    )

    download_csv(df_man.rename(columns={"Maquina": "maquina", "Data": "data", "Tipo": "tipo", "Custo": "custo"}), filename="dashboard_manutencao.csv", key="bi_manut_csv")

    # Quick summary of ordens de servico
    try:
        ords = pd.DataFrame(ordens)
    except Exception:
        ords = pd.DataFrame()

    if not ords.empty:
        # try to extract a date field if present
        date_cols = [c for c in ords.columns if "data" in c.lower()]
        if date_cols:
            col_date = date_cols[0]
            ords[col_date] = pd.to_datetime(ords[col_date], errors="coerce").dt.date
            mask = pd.Series(True, index=ords.index)
            if start is not None:
                mask &= ords[col_date].notna() & (ords[col_date] >= start)
            if end is not None:
                mask &= ords[col_date].notna() & (ords[col_date] <= end)
            ords = ords[mask]
        st.subheader("Ordens de serviço")
        st.caption(f"{len(ords)} ordem(ns) no período selecionado.")
        st.dataframe(ords, hide_index=True)

