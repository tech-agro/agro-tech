"""BI dashboard: Margem por safra.

Calcula margem por safra aproximada como:
  margem = receita_vendas - custo_insumos (compras) - custo_manutencao - custo_logistica

Premissas (documentadas no expander):
- Receita é agregada a partir dos itens de venda (quantidade * valor_unitario) e alocada à safra
  do lote do item quando disponível; caso contrário a venda é atribuída a "Fora de safra".
- Custo de insumos é a soma das compras (invoices) e é alocada por data da compra ao intervalo
  da safra (quando houver correspondência pela data), caso contrário "Fora de safra".
- Custo de logística usa o custo previsto das operações do módulo de logística e é alocado
  às safras pelos lotes envolvidos (mesma regra do dashboard de logística).
- Custo de manutenção é obtido a partir das ordens de manutenção quando disponível; se não
  houver dados é mostrado como 0. Usuário pode excluir/alterar componentes via filtros.

Este dashboard é intencionalmente conservador: soma custos diretamente atribuíveis e deixa
especificidades (alocação por proporcionalidade entre safras, rateios complexos) para etapas
futuras.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from components.bi import charts
from components.bi.filters import render_filter_bar
from components.bi.widgets import delta_label, download_csv, fmt_brl, fmt_int
from components.shared.palette import semantic
from components.shared.screens import setup_page, toast_error
from services import producao_client as producao_api
from services.compras_client import PurchasesClient, PurchasesApiError
from services.comercial_client import ComercialClient, ComercialApiError
from services.logistica_client import LogisticsClient, LogisticsApiError
from services.estoque_client import EstoqueClient, EstoqueApiError
from services import manutencao_client as manutencao_api

_FORA_SAFRA = "Fora de safra"


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
def _list_purchases_cached() -> list:
    return PurchasesClient().list_purchases()


@st.cache_data(ttl=60)
def _list_vendas_cached() -> list:
    return ComercialClient().list_vendas()


@st.cache_data(ttl=60)
def _list_operations_cached() -> list:
    return LogisticsClient().list_operations()


@st.cache_data(ttl=60)
def _list_loads_cached() -> list:
    """Cached wrapper for listing all cargas (loads) from logistics client."""
    try:
        return LogisticsClient().list_all_loads()
    except Exception:
        return []


@st.cache_data(ttl=60)
def _fetch_vendas_details(ids: tuple[int, ...]) -> list:
    """Fetch full venda (with items) for each id. Cached by tuple of ids."""
    client = ComercialClient()
    resultados: list = []
    for id_v in ids:
        try:
            resultados.append(client.get_venda(int(id_v)))
        except Exception:
            # skip failures; caller will still have partial data
            pass
    return resultados


@st.cache_data(ttl=60)
def _list_manutencoes_cached() -> list[dict]:
    try:
        corretivas = manutencao_api.list_manutencoes_corretivas()
        preventivas = manutencao_api.list_manutencoes_preventivas()
        return corretivas + preventivas
    except Exception:
        st.warning("Nao foi possivel carregar os dados de manutencao.")
        return []


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


def _safra_label(item: dict) -> str:
    return f"{item.get('nome', 'Safra')} ({item.get('ano', '')})"


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
    # pd.to_datetime on a scalar should return a pd.Timestamp; ensure we handle types safely
    if isinstance(parsed, pd.Timestamp):
        return parsed.to_pydatetime().date()
    # fallback: if parsed exposes a .date() method, call and coerce result to date
    try:
        maybe_date = getattr(parsed, "date", None)
        if callable(maybe_date):
            res = maybe_date()
            if isinstance(res, date):
                return res
            # try coercing via pandas (handles Timestamp and string-like results)
            coerced = pd.to_datetime(str(res), errors="coerce")
            if not pd.isna(coerced):
                return coerced.to_pydatetime().date()
    except Exception:
        pass
    return None


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


def _assign_safra_by_date(day: date | None, safras: list[dict]) -> str:
    if day is None:
        return _FORA_SAFRA
    for safra in safras:
        inicio = _as_date(safra.get("dt_inicio"))
        fim = _as_date(safra.get("dt_fim"))
        if inicio is None or fim is None:
            continue
        if inicio <= day <= fim:
            return _safra_label(safra)
    return _FORA_SAFRA


def _slice_period(df: pd.DataFrame, start: date | None, end: date | None) -> pd.DataFrame:
    """Return rows whose Data lies between start and end (inclusive).

    Converts start/end to pandas timestamps so comparisons with datetime64 columns
    are valid. If df["Data"] is not datetime, pandas will attempt to compare anyway.
    """
    if df.empty:
        return df
    if start is None and end is None:
        return df
    mask = df["Data"].notna()
    if start is not None:
        # pd.Timestamp accepts date/datetime scalars reliably
        start_ts = pd.Timestamp(start)
        mask &= df["Data"] >= start_ts
    if end is not None:
        end_ts = pd.Timestamp(end)
        mask &= df["Data"] <= end_ts
    return df[mask]


def render() -> None:
    setup_page("Margem por safra", "Indicador de margem por safra: receita menos custos atribuiveis.")

    try:
        purchases = _list_purchases_cached()
        vendas = _list_vendas_cached()
        operations = _list_operations_cached()
    except (PurchasesApiError, ComercialApiError, LogisticsApiError) as exc:
        toast_error(exc)
        st.stop()

    lotes = _list_lotes_cached()
    safras, lot_to_safra = _load_lot_safra_map(lotes)
    safra_by_id = {int(item["id_safra"]): _safra_label(item) for item in safras}

    # If vendas listing does not include itens, fetch details per venda (fallback).
    if vendas:
        sample = vendas[0]
        if not getattr(sample, "itens", None):
            ids_list: list[int] = []
            for v in vendas:
                id_val = getattr(v, "id_venda", getattr(v, "id", None))
                if id_val is None:
                    continue
                try:
                    ids_list.append(int(id_val))
                except Exception:
                    # ignore non-integer ids
                    continue
            ids = tuple(ids_list)
            if ids:
                detailed = _fetch_vendas_details(ids)
                if detailed:
                    vendas = detailed

    # --- Build revenue rows from vendas items ---
    revenue_rows: list[dict] = []
    for v in vendas:
        data_venda = _as_date(getattr(v, "data_venda", None))
        # venda has itens attribute
        itens = getattr(v, "itens", []) or []
        for item in itens:
            quantidade = float(getattr(item, "quantidade", 0.0) or 0.0)
            valor_unit = float(getattr(item, "valor_unitario", 0.0) or 0.0)
            valor = quantidade * valor_unit
            lote_id = getattr(item, "id_lote", None)
            safra_nome = _FORA_SAFRA
            if lote_id:
                id_s = lot_to_safra.get(int(lote_id))
                if id_s is not None:
                    safra_nome = safra_by_id.get(id_s, _FORA_SAFRA)
                else:
                    safra_nome = _assign_safra_by_date(data_venda, safras)
            else:
                safra_nome = _assign_safra_by_date(data_venda, safras)

            revenue_rows.append({
                "Data": data_venda,
                "Safra": safra_nome,
                "Produto": getattr(item, "produto_nome", f"#{getattr(item, 'id_produto', '')}"),
                "Valor": valor,
            })

    # --- Purchases (insumos) by purchase date assigned to safra interval ---
    purchase_rows: list[dict] = []
    for p in purchases:
        data_compra = _as_date(getattr(p, "data_compra", None)) or _as_date(getattr(p, "data_emissao", None))
        safra_nome = _assign_safra_by_date(data_compra, safras)
        # Purchases may have valor_total
        valor_total = float(getattr(p, "valor_total", 0.0) or 0.0)
        purchase_rows.append({"Data": data_compra, "Safra": safra_nome, "Valor": valor_total})

    # --- Manutenção: corretivas e preventivas (apenas finalizadas) ---
    manutencoes = _list_manutencoes_cached()
    manutencao_rows: list[dict] = []
    for m in manutencoes:
        base = m.get("manutencao") or {}
        if base.get("status") != "CONCLUIDA":
            continue
        data_ref = _as_date(base.get("dt_inicio"))
        safra_nome = _assign_safra_by_date(data_ref, safras)
        valor = float(base.get("custo") or 0.0)
        manutencao_rows.append({"Data": data_ref, "Safra": safra_nome, "Valor": valor})

    # --- Logistics costs from operations (like logistica dashboard) ---
    try:
        loads = _list_loads_cached()
    except Exception:
        loads = []

    loads_by_op: dict[int, list] = defaultdict(list)
    for load in loads:
        loads_by_op[load.id_operacao].append(load)

    logistics_rows: list[dict] = []
    for op in operations:
        op_loads = loads_by_op.get(getattr(op, "id_operacao"), [])
        safra_nome = _operation_safra(op_loads, lot_to_safra, safra_by_id)
        data_ref = _as_date(getattr(op, "data_inicio", None)) or _as_date(getattr(op, "data_fim", None))
        valor = float(getattr(op, "custo_previsto", 0.0) or 0.0)
        logistics_rows.append({"Data": data_ref, "Safra": safra_nome, "Valor": valor})

    # Create DataFrames
    df_rev_all = pd.DataFrame(revenue_rows)
    df_pur_all = pd.DataFrame(purchase_rows)
    df_log_all = pd.DataFrame(logistics_rows)
    df_man_all = pd.DataFrame(manutencao_rows)

    # Filters
    safra_options = sorted({row["Safra"] for row in revenue_rows} | {row["Safra"] for row in purchase_rows} | {row["Safra"] for row in logistics_rows} | {row["Safra"] for row in manutencao_rows}) if (revenue_rows or purchase_rows or logistics_rows or manutencao_rows) else [ _FORA_SAFRA ]
    filtros = render_filter_bar(prefix="bi_margem", safra_options=safra_options, product_options=[])

    # Ensure Data columns are datetime (coerce invalids to NaT) before slicing the period.
    if not df_rev_all.empty:
        df_rev_all = df_rev_all.copy()
        df_rev_all["Data"] = pd.to_datetime(df_rev_all["Data"], errors="coerce")
        df_rev = _slice_period(df_rev_all, filtros.start, filtros.end)
    else:
        df_rev = df_rev_all

    if not df_pur_all.empty:
        df_pur_all = df_pur_all.copy()
        df_pur_all["Data"] = pd.to_datetime(df_pur_all["Data"], errors="coerce")
        df_pur = _slice_period(df_pur_all, filtros.start, filtros.end)
    else:
        df_pur = df_pur_all

    if not df_log_all.empty:
        df_log_all = df_log_all.copy()
        df_log_all["Data"] = pd.to_datetime(df_log_all["Data"], errors="coerce")
        df_log = _slice_period(df_log_all, filtros.start, filtros.end)
    else:
        df_log = df_log_all

    # maintenance DataFrame handling
    if not df_man_all.empty:
        df_man_all = df_man_all.copy()
        df_man_all["Data"] = pd.to_datetime(df_man_all["Data"], errors="coerce")
        df_man = _slice_period(df_man_all, filtros.start, filtros.end)
    else:
        df_man = df_man_all

    if filtros.safra:
        df_rev = df_rev[df_rev["Safra"] == filtros.safra]
        df_pur = df_pur[df_pur["Safra"] == filtros.safra]
        df_log = df_log[df_log["Safra"] == filtros.safra]
        df_man = df_man[df_man["Safra"] == filtros.safra]

    # Aggregations
    receita = float(df_rev["Valor"].sum()) if not df_rev.empty else 0.0
    custo_insumos = float(df_pur["Valor"].sum()) if not df_pur.empty else 0.0
    custo_logistica = float(df_log["Valor"].sum()) if not df_log.empty else 0.0
    custo_manutencao = float(df_man["Valor"].sum()) if not df_man.empty else 0.0

    margem = receita - custo_insumos - custo_logistica - custo_manutencao

    # Previous period comparison
    prev_start, prev_end = filtros.previous_span()
    prev_rev = df_rev_all if prev_start is None else _slice_period(df_rev_all, prev_start, prev_end)
    prev_pur = df_pur_all if prev_start is None else _slice_period(df_pur_all, prev_start, prev_end)
    prev_log = df_log_all if prev_start is None else _slice_period(df_log_all, prev_start, prev_end)
    receita_prev = float(prev_rev["Valor"].sum()) if not prev_rev.empty else 0.0
    custo_insumos_prev = float(prev_pur["Valor"].sum()) if not prev_pur.empty else 0.0
    custo_logistica_prev = float(prev_log["Valor"].sum()) if not prev_log.empty else 0.0
    prev_man = df_man_all if prev_start is None else _slice_period(df_man_all, prev_start, prev_end)
    custo_manutencao_prev = float(prev_man["Valor"].sum()) if not prev_man.empty else 0.0
    margem_prev = receita_prev - custo_insumos_prev - custo_logistica_prev - custo_manutencao_prev

    with st.container(horizontal=True):
        st.metric("Receita", fmt_brl(receita), delta=delta_label(receita, receita_prev, formatter=fmt_brl), border=True)
        st.metric("Custo insumos", fmt_brl(custo_insumos), delta=delta_label(custo_insumos, custo_insumos_prev, formatter=fmt_brl), delta_color="inverse", border=True)
        st.metric("Custo logistica", fmt_brl(custo_logistica), delta=delta_label(custo_logistica, custo_logistica_prev, formatter=fmt_brl), delta_color="inverse", border=True)
        st.metric("Custo manutencao", fmt_brl(custo_manutencao), delta=delta_label(custo_manutencao, custo_manutencao_prev, formatter=fmt_brl), delta_color="inverse", border=True)
        st.metric(
            "Margem",
            fmt_brl(margem),
            delta=delta_label(margem, margem_prev, formatter=fmt_brl),
            help="Receita − custo de insumos − custo de logística − custo de manutenção.",
            border=True,
        )

    # Inform user if no maintenance records were found
    if df_man_all.empty:
        st.info("Nenhum custo de manutenção concluída encontrado para os dados atuais.")

    st.divider()

    # Margin by safra breakdown
    safra_set = set()
    for df, label in ((df_rev, "Receita"), (df_pur, "Insumos"), (df_log, "Logistica"), (df_man, "Manutencao")):
        if df is None or df.empty:
            continue
        grouped = df.groupby("Safra", as_index=False)["Valor"].sum()
        for _, row in grouped.iterrows():
            safra_set.add(row["Safra"])
    if not safra_set:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
        return

    safra_list = sorted(safra_set)
    rows = []
    for s in safra_list:
        rec = round(float(df_rev[df_rev["Safra"] == s]["Valor"].sum()), 2) if not df_rev.empty else 0.0
        pur = round(float(df_pur[df_pur["Safra"] == s]["Valor"].sum()), 2) if not df_pur.empty else 0.0
        log = round(float(df_log[df_log["Safra"] == s]["Valor"].sum()), 2) if not df_log.empty else 0.0
        man = round(float(df_man[df_man["Safra"] == s]["Valor"].sum()), 2) if not df_man.empty else 0.0
        marg = round(rec - pur - log - man, 2)
        rows.append({"Safra": s, "Receita": rec, "Insumos": pur, "Logistica": log, "Manutencao": man, "Margem": marg})

    df_table = pd.DataFrame(rows).sort_values("Margem", ascending=False)

    col_chart, col_table = st.columns([1.2, 1])
    with col_chart:
        st.subheader("Margem por safra")
        df_chart = df_table.copy()
        df_chart["Resultado"] = df_chart["Margem"].apply(lambda m: "Positiva" if m >= 0 else "Negativa")
        charts.bar_chart(
            df_chart,
            x="Safra",
            y="Margem",
            y_title="Margem (R$)",
            color="Resultado",
            color_map={"Positiva": semantic("green"), "Negativa": semantic("red")},
        )

    with col_table:
        st.subheader("Detalhamento por componente")
        st.dataframe(
            df_table,
            hide_index=True,
            column_config={
                "Safra": st.column_config.TextColumn("Safra", pinned=True),
                "Receita": st.column_config.NumberColumn("Receita (R$)", format="localized"),
                "Insumos": st.column_config.NumberColumn("Insumos (R$)", format="localized"),
                "Logistica": st.column_config.NumberColumn("Logística (R$)", format="localized"),
                "Manutencao": st.column_config.NumberColumn("Manutenção (R$)", format="localized"),
                "Margem": st.column_config.NumberColumn("Margem (R$)", format="localized"),
            },
        )
        download_csv(
            df_table.rename(columns={"Safra": "safra", "Receita": "receita", "Insumos": "insumos", "Logistica": "logistica", "Manutencao": "manutencao", "Margem": "margem"}),
            filename="dashboard_margem_safra.csv",
            key="bi_margem_csv",
        )

    # Document assumptions
    with st.expander("Premissas e regras de alocacao"):
        st.markdown(
            """
- Receita: soma dos itens de venda (quantidade * valor unitario). Alocada à safra do lote quando presente, caso contrario por data da venda à safra cujo intervalo contenha a data.
- Insumos: soma das compras (valor_total) alocada pela data da compra ao intervalo de safra correspondente.
- Logistica: usa o custo previsto das operacoes e aloca por lotes envolvidos (mesma regra do dashboard de Logistica).
- Manutencao: soma do custo de manutencoes com status CONCLUIDA (corretivas e preventivas), alocada pela data de inicio (dt_inicio) ao intervalo da safra correspondente — mesma regra usada para insumos.
- Limitações: rateios entre safras (quando uma operacao envolve multiplos lotes de safras diferentes) sao aproximados pela escolha da primeira safra detectada; isso pode ser refinado futuramente.
"""
        )


