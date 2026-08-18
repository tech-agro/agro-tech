"""BI dashboard for Comercial: receita e desempenho de vendas."""

from __future__ import annotations

from datetime import date
from collections import defaultdict

import pandas as pd
import streamlit as st

from components.bi.filters import render_filter_bar, chart_select_key
from components.bi.charts import bar_chart, line_chart
from components.bi.widgets import delta_label, download_csv, fmt_brl, fmt_int
from components.shared.screens import setup_page, toast_error
from services.comercial_client import ComercialClient, ComercialApiError
from services.compras_client import PurchasesClient
from services import producao_client as producao_api


@st.cache_data(ttl=60)
def _list_vendas_cached() -> list:
    return ComercialClient().list_vendas()


@st.cache_data(ttl=60)
def _fetch_venda_details(id_venda: int):
    try:
        return ComercialClient().get_venda(int(id_venda))
    except Exception:
        return None


@st.cache_data(ttl=60)
def _list_products_cached() -> list:
    try:
        return ComercialClient().list_produtos()
    except Exception:
        return []


@st.cache_data(ttl=60)
def _load_safras_cached() -> list[dict]:
    try:
        return producao_api.listar("/safras")
    except Exception:
        return []


def _as_date(value):
    if value is None:
        return None
    try:
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return None
        try:
            return ts.date()
        except Exception:
            # fallback: try parsing the YYYY-MM-DD portion
            text = str(value).split("T")[0][:10]
            parsed = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
            return parsed.date() if not pd.isna(parsed) else None
    except Exception:
        return None


def _safe_float(value) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except Exception:
        try:
            return float(str(value))
        except Exception:
            return 0.0


def _safra_label(item: dict) -> str:
    return f"{item.get('nome', 'Safra')} ({item.get('ano', '')})"


def _assign_safra_by_date(day: date | None, safras: list[dict]) -> str:
    if day is None:
        return "Fora de safra"
    for safra in safras:
        inicio = _as_date(safra.get("dt_inicio"))
        fim = _as_date(safra.get("dt_fim"))
        if inicio is None or fim is None:
            continue
        if inicio <= day <= fim:
            return _safra_label(safra)
    return "Fora de safra"


def render() -> None:
    setup_page("Comercial", "Indicadores comerciais: receita, ticket medio e vendas por produto/safra")

    try:
        vendas = _list_vendas_cached()
    except ComercialApiError as exc:
        toast_error(exc)
        st.stop()

    products = _list_products_cached()
    safras = _load_safras_cached()

    # If vendas don't include itens, try to fetch details for each venda (cached)
    detailed = []
    fallback_needed = False
    if vendas:
        sample = vendas[0]
        if not getattr(sample, "itens", None):
            fallback_needed = True
    if fallback_needed:
        for v in vendas:
            id_v = getattr(v, "id_venda", getattr(v, "id", None))
            if id_v is None:
                continue
            detail = _fetch_venda_details(int(id_v))
            if detail is not None:
                detailed.append(detail)
        if detailed:
            vendas = detailed

    # Build rows of venda items for analysis
    rows = []
    for v in vendas:
        data_venda = _as_date(getattr(v, "data_venda", None))
        id_venda = getattr(v, "id_venda", getattr(v, "id", None))
        cliente = getattr(v, "cliente_nome", f"#{getattr(v, 'id_cliente', '')}")
        itens = getattr(v, "itens", []) or []
        for item in itens:
            produto = getattr(item, "produto_nome", f"#{getattr(item, 'id_produto', '')}")
            quantidade = _safe_float(getattr(item, "quantidade", 0.0))
            valor_unit = _safe_float(getattr(item, "valor_unitario", 0.0))
            valor = quantidade * valor_unit
            safra = _assign_safra_by_date(data_venda, safras)
            rows.append({"Data": data_venda, "Cliente": cliente, "Produto": produto, "Quantidade": quantidade, "Valor": valor, "Safra": safra, "IdVenda": id_venda})

    df_all = pd.DataFrame(rows)

    product_options = sorted({r["Produto"] for r in rows}) if rows else []
    cliente_options = sorted({r["Cliente"] for r in rows}) if rows else []
    safra_options = sorted({r["Safra"] for r in rows}) if rows else ["Fora de safra"]

    filtros = render_filter_bar(prefix="bi_comercial", safra_options=safra_options, product_options=product_options, cliente_options=cliente_options)

    # Ensure Data is datetime
    if not df_all.empty:
        df_all = df_all.copy()
        df_all["Data"] = pd.to_datetime(df_all["Data"], errors="coerce")
    df = df_all
    if filtros.start or filtros.end:
        df = df[df["Data"].notna()]
        if filtros.start:
            df = df[df["Data"] >= pd.Timestamp(filtros.start)]
        if filtros.end:
            df = df[df["Data"] <= pd.Timestamp(filtros.end)]
    if filtros.safra:
        df = df[df["Safra"] == filtros.safra]
    if filtros.product:
        df = df[df["Produto"] == filtros.product]
    if getattr(filtros, "cliente", None):
        df = df[df["Cliente"] == filtros.cliente]

    # KPIs
    receita = float(df["Valor"].sum()) if not df.empty else 0.0
    n_vendas = int(df["IdVenda"].nunique()) if not df.empty and "IdVenda" in df.columns else (int(df.drop_duplicates(subset=["Data", "Cliente"]).shape[0]) if not df.empty else 0)
    ticket_medio = receita / n_vendas if n_vendas else None
    clientes_receita = df.groupby("Cliente", as_index=False).agg({"Valor": "sum"})
    if not clientes_receita.empty:
        clientes_receita = clientes_receita.sort_values(by="Valor", ascending=False)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita total", fmt_brl(receita))
    col2.metric("Ticket medio", fmt_brl(ticket_medio) if ticket_medio is not None else "R$ 0,00")
    col3.metric("Clientes (ativos)", fmt_int(clientes_receita.shape[0]))
    col4.metric("Produtos vendidos", fmt_int(df["Produto"].nunique() if not df.empty else 0))

    st.divider()

    # Revenue by client
    st.subheader("Receita por cliente")
    if not clientes_receita.empty:
        bar_chart(clientes_receita, x="Cliente", y="Valor", title="Receita por cliente")
    else:
        st.info("Nenhuma venda encontrada para os filtros selecionados.")

    st.divider()

    # Sales by product
    st.subheader("Vendas por produto")
    if not df.empty:
        by_prod = df.groupby("Produto", as_index=False).agg({"Valor": "sum", "Quantidade": "sum"})
        by_prod = by_prod.sort_values(by="Valor", ascending=False)
        bar_chart(by_prod, x="Produto", y="Valor", title="Valor por produto")
        st.subheader("Quantidade por produto")
        bar_chart(by_prod, x="Produto", y="Quantidade", title="Quantidade vendida por produto")
    
    # Sales over time by safra
    st.divider()
    st.subheader("Receita por safra no tempo")
    if not df.empty:
        times = df.groupby([pd.Grouper(key="Data", freq="ME"), "Safra"]).agg({"Valor": "sum"}).reset_index()
        # convert period to timestamp at month end
        times["Data"] = times["Data"].dt.to_period("M").dt.to_timestamp(how="end")
        line_chart(times, x="Data", y="Valor", color="Safra")
    
    st.divider()
    st.subheader("Tabela de vendas")
    if not df.empty:
        display = df.copy()
        display["Valor"] = pd.to_numeric(display["Valor"], errors="coerce").fillna(0.0).astype(float)
        st.dataframe(display, use_container_width=True, hide_index=True)
        download_csv(display.rename(columns={"Data": "data", "Cliente": "cliente", "Produto": "produto", "Quantidade": "quantidade", "Valor": "valor", "Safra": "safra"}), filename="dashboard_comercial.csv", key="bi_comercial_csv")
    else:
        st.info("Nenhuma venda para exibir.")
