"""BI dashboard for the purchases module."""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from app.compras.enum import PurchaseType
from components.bi import charts
from components.bi.filters import (
    apply_bar_click,
    apply_month_click,
    chart_select_key,
    render_filter_bar,
)
from components.bi.widgets import (
    delta_label,
    download_csv,
    fmt_brl,
    fmt_int,
    fmt_qty,
    unit_label,
)
from components.shared.screens import setup_page, toast_error
from services import producao_client as producao_api
from services.compras_client import PurchasesApiError, PurchasesClient

_FORA_SAFRA = "Fora de safra"
_SANKEY_MIN_NODES = 3


@st.cache_data
def _aggregate_supplier_bubbles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Fornecedor", "Pedidos", "Ticket medio", "Valor"])
    grouped = df.groupby("Fornecedor", as_index=False).agg(
        Pedidos=("id_pedido", "nunique"),
        Valor=("Valor", "sum"),
    )
    grouped = grouped[grouped["Pedidos"] > 0]
    grouped["Ticket medio"] = grouped["Valor"] / grouped["Pedidos"]
    return grouped.sort_values("Valor", ascending=False)


@st.cache_data
def _aggregate_purchase_flow(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Fornecedor", "Produto", "Valor"])
    return (
        df.groupby(["Fornecedor", "Produto"], as_index=False)["Valor"]
        .sum()
        .sort_values("Valor", ascending=False)
    )


def _client() -> PurchasesClient:
    return PurchasesClient()


def _as_date(value) -> date | None:
    if value is None or (not isinstance(value, date) and pd.isna(value)):
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


def _load_safras() -> list[dict]:
    try:
        return producao_api.listar("/safras")
    except Exception:
        st.warning("Nao foi possivel carregar as safras para o filtro.")
        return []


def _assign_safra(day: date | None, safras: list[dict]) -> str:
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


def render() -> None:
    setup_page("Compras", "Acompanhamento de aquisicao de insumos")

    client = _client()
    try:
        orders = client.list_orders()
        purchases = client.list_purchases()
        items = client.list_all_order_items()
        products = client.list_products()
        suppliers = client.list_suppliers()
    except PurchasesApiError as exc:
        toast_error(exc)
        st.stop()

    safras = _load_safras()
    orders_by_id = {order.id_pedido: order for order in orders}
    items_by_order: dict[int, list] = {}
    for item in items:
        items_by_order.setdefault(item.id_pedido, []).append(item)

    product_options = sorted({p.nome for p in products})
    supplier_options = sorted({s.nome for s in suppliers})
    rank_key = chart_select_key("bi_compras", "rank_fornecedores")
    produto_key = chart_select_key("bi_compras", "valor_produto")
    bubble_key = chart_select_key("bi_compras", "fornecedores_bubble")
    mes_key = chart_select_key("bi_compras", "custo_mensal")
    apply_bar_click(
        prefix="bi_compras",
        field="fornecedor",
        chart_key=rank_key,
        allowed=supplier_options,
    )
    apply_bar_click(
        prefix="bi_compras",
        field="produto",
        chart_key=produto_key,
        allowed=product_options,
    )
    apply_bar_click(
        prefix="bi_compras",
        field="fornecedor",
        chart_key=bubble_key,
        point_field="legendgroup",
        allowed=supplier_options,
    )
    apply_month_click(prefix="bi_compras", chart_key=mes_key)
    filtros = render_filter_bar(
        prefix="bi_compras",
        safra_options=[_safra_label(s) for s in safras] + [_FORA_SAFRA],
        product_options=product_options,
        supplier_options=supplier_options,
    )

    rows = []
    for purchase in purchases:
        order = orders_by_id.get(purchase.id_pedido)
        if order is None:
            continue
        if order.tipo_compra == PurchaseType.EQUIPAMENTO:
            continue
        data = _as_date(purchase.data_compra) or _as_date(order.data_pedido)
        safra_nome = _assign_safra(data, safras)
        if filtros.safra and safra_nome != filtros.safra:
            continue
        fornecedor = order.fornecedor_nome or f"#{order.id_fornecedor}"
        if filtros.supplier and fornecedor != filtros.supplier:
            continue
        for item in items_by_order.get(purchase.id_pedido, []):
            produto = item.produto_nome or f"#{item.id_produto}"
            if filtros.product and produto != filtros.product:
                continue
            quantidade = float(item.quantidade)
            valor = quantidade * float(item.valor_unitario)
            rows.append(
                {
                    "Data": data,
                    "Safra": safra_nome,
                    "Fornecedor": fornecedor,
                    "Produto": produto,
                    "id_pedido": purchase.id_pedido,
                    "Volume": quantidade,
                    "Unidade": unit_label(item.unidade_sigla),
                    "Valor": valor,
                    "Custo unitario": float(item.valor_unitario),
                }
            )

    df_all = pd.DataFrame(rows)
    df = _slice_period(df_all, filtros.start, filtros.end)
    prev_start, prev_end = filtros.previous_span()
    df_prev = (
        _slice_period(df_all, prev_start, prev_end)
        if prev_start is not None and prev_end is not None
        else pd.DataFrame(columns=df_all.columns if not df_all.empty else [])
    )
    has_previous = prev_start is not None

    valor_total = float(df["Valor"].sum()) if not df.empty else 0.0
    valor_prev = float(df_prev["Valor"].sum()) if not df_prev.empty else 0.0
    n_pedidos = int(df["id_pedido"].nunique()) if not df.empty else 0
    n_pedidos_prev = int(df_prev["id_pedido"].nunique()) if not df_prev.empty else 0
    n_fornecedores = int(df["Fornecedor"].nunique()) if not df.empty else 0
    n_fornecedores_prev = int(df_prev["Fornecedor"].nunique()) if not df_prev.empty else 0
    ticket_medio = (valor_total / n_pedidos) if n_pedidos > 0 else None
    ticket_medio_prev = (valor_prev / n_pedidos_prev) if n_pedidos_prev > 0 else None

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric(
        "Valor comprado",
        fmt_brl(valor_total),
        delta=delta_label(valor_total, valor_prev, formatter=fmt_brl) if has_previous else None,
    )
    col_m2.metric(
        "N de pedidos",
        str(n_pedidos),
        delta=(
            delta_label(n_pedidos, n_pedidos_prev, formatter=fmt_int)
            if has_previous
            else None
        ),
        help="Quantidade de pedidos no recorte. Independente da unidade do produto.",
    )
    col_m3.metric(
        "Fornecedores",
        str(n_fornecedores),
        delta=(
            delta_label(n_fornecedores, n_fornecedores_prev, formatter=fmt_int)
            if has_previous
            else None
        ),
    )
    col_m4.metric(
        "Ticket medio",
        fmt_brl(ticket_medio) if ticket_medio is not None else "—",
        delta=(
            delta_label(ticket_medio, ticket_medio_prev, formatter=fmt_brl)
            if has_previous
            else None
        ),
        help="Valor comprado dividido pelo numero de pedidos. Valido com qualquer mix de produtos.",
    )

    col_rank, col_secundario = st.columns(2)
    with col_rank:
        st.subheader("Ranking de fornecedores")
        df_rank = (
            df.groupby("Fornecedor", as_index=False)["Valor"].sum().sort_values(
                "Valor", ascending=False
            )
            if not df.empty
            else pd.DataFrame()
        )
        charts.bar_chart(
            df_rank,
            x="Fornecedor",
            y="Valor",
            y_title="Valor (R$)",
            x_title=None,
            select_key=rank_key,
        )
    with col_secundario:
        if filtros.product:
            st.subheader("Volume × valor")
            df_scatter = (
                df.groupby("Fornecedor", as_index=False)
                .agg(Volume=("Volume", "sum"), Valor=("Valor", "sum"))
                if not df.empty
                else pd.DataFrame()
            )
            charts.scatter_chart(
                df_scatter,
                x="Volume",
                y="Valor",
                color="Fornecedor" if not df_scatter.empty else None,
                hover_name="Fornecedor",
                x_title="Volume",
                y_title="Valor (R$)",
            )
        else:
            st.subheader("Valor por produto")
            df_produto = (
                df.groupby("Produto", as_index=False)["Valor"].sum().sort_values(
                    "Valor", ascending=False
                )
                if not df.empty
                else pd.DataFrame()
            )
            charts.bar_chart(
                df_produto,
                x="Produto",
                y="Valor",
                y_title="Valor (R$)",
                x_title=None,
                select_key=produto_key,
            )

    st.subheader("Fornecedores (pedidos × ticket)")
    if df.empty:
        charts.scatter_chart(pd.DataFrame(), x="Pedidos", y="Ticket medio")
    else:
        df_bubble = _aggregate_supplier_bubbles(df[["Fornecedor", "id_pedido", "Valor"]])
        charts.scatter_chart(
            df_bubble,
            x="Pedidos",
            y="Ticket medio",
            color="Fornecedor" if not df_bubble.empty else None,
            size="Valor" if not df_bubble.empty else None,
            hover_name="Fornecedor",
            hover_data=["Valor"],
            x_title="N de pedidos",
            y_title="Ticket medio (R$)",
            height=360,
            select_key=bubble_key,
        )
        st.caption(
            "Eixo X: quantidade de pedidos. Eixo Y: ticket medio (valor / pedidos). "
            "Tamanho da bolha: valor total comprado."
        )

    if not df.empty:
        st.subheader("Custo de insumos por mes")
        df_mes = df.dropna(subset=["Data"]).copy()
        if df_mes.empty:
            st.info("Nenhuma compra com data no periodo.")
        else:
            df_mes["Mes"] = pd.to_datetime(df_mes["Data"]).dt.to_period("M").dt.to_timestamp()
            mensal = df_mes.groupby("Mes", as_index=False)["Valor"].sum()
            inicio_mes = pd.Timestamp(filtros.start or df_mes["Data"].min()).replace(day=1)
            fim_mes = pd.Timestamp(filtros.end or date.today()).replace(day=1)
            meses = pd.DataFrame({"Mes": pd.date_range(inicio_mes, fim_mes, freq="MS")})
            mensal = meses.merge(mensal, on="Mes", how="left").fillna({"Valor": 0.0})
            charts.line_chart(
                mensal,
                x="Mes",
                y="Valor",
                x_title=None,
                y_title="Valor (R$)",
                select_key=mes_key,
            )

    if not df.empty:
        df_flow = _aggregate_purchase_flow(df[["Fornecedor", "Produto", "Valor"]])
        n_fontes = int(df_flow["Fornecedor"].nunique()) if not df_flow.empty else 0
        n_alvos = int(df_flow["Produto"].nunique()) if not df_flow.empty else 0
        compacto = n_fontes < _SANKEY_MIN_NODES or n_alvos < _SANKEY_MIN_NODES

        def _render_sankey() -> None:
            charts.sankey_chart(
                df_flow,
                source="Fornecedor",
                target="Produto",
                value="Valor",
            )
            st.caption("Espessura do fluxo: valor comprado (R$). Cor da origem: fornecedor.")

        if compacto:
            with st.expander("Ver fluxo de compras"):
                _render_sankey()
        else:
            st.subheader("Fluxo de compras")
            _render_sankey()

    st.subheader("Detalhamento")
    if df.empty:
        st.info("Nenhuma compra no recorte selecionado.")
        return

    detalhe = df.copy()
    export = detalhe.copy()
    detalhe["Data"] = detalhe["Data"].map(
        lambda d: d.strftime("%d/%m/%Y") if d else ""
    )
    detalhe["Volume"] = detalhe["Volume"].map(fmt_qty)
    detalhe["Valor"] = detalhe["Valor"].map(fmt_brl)
    detalhe["Custo unitario"] = detalhe["Custo unitario"].map(fmt_brl)
    export["Data"] = export["Data"].map(
        lambda d: d.strftime("%d/%m/%Y") if d else ""
    )
    colunas = [
        "Data",
        "Safra",
        "Fornecedor",
        "Produto",
        "Volume",
        "Unidade",
        "Valor",
        "Custo unitario",
    ]
    st.dataframe(
        detalhe[colunas],
        use_container_width=True,
        hide_index=True,
    )
    download_csv(
        export[colunas],
        filename="compras-detalhamento.csv",
        key="bi_compras_csv",
    )
