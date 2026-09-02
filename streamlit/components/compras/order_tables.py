"""DataFrames for purchases list and item detail views."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.compras.formatters import (
    ORDER_STATUS_OPTIONS,
    ORDER_STATUS_TONE,
    PURCHASE_TYPE_LABELS,
    order_status_label,
)
from components.shared.palette import badge_column, badge_value


def orders_df(orders) -> pd.DataFrame:
    if not orders:
        return pd.DataFrame(columns=["ID", "Fornecedor", "Tipo", "Data", "Status"])
    return pd.DataFrame(
        [
            {
                "ID": o.id_pedido,
                "Fornecedor": o.fornecedor_nome or f"#{o.id_fornecedor}",
                "Tipo": PURCHASE_TYPE_LABELS.get(
                    o.tipo_compra, getattr(o.tipo_compra, "value", "Insumo")
                ),
                "Data": o.data_pedido,
                "Status": badge_value(order_status_label(o.status)),
            }
            for o in orders
        ]
    )


def orders_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Fornecedor": st.column_config.TextColumn("Fornecedor", pinned=True),
        "Tipo": st.column_config.TextColumn("Tipo"),
        "Data": st.column_config.DateColumn("Data do pedido", format="DD/MM/YYYY"),
        "Status": badge_column("Status", ORDER_STATUS_OPTIONS, ORDER_STATUS_TONE, width="medium"),
    }


def items_view_df(items) -> pd.DataFrame:
    columns = [
        "ID produto",
        "Produto",
        "Quantidade",
        "Unidade de medida",
        "Valor unitario",
        "Subtotal",
    ]
    if not items:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID produto": i.id_produto,
                "Produto": i.produto_nome or f"#{i.id_produto}",
                "Quantidade": float(i.quantidade),
                "Unidade de medida": i.unidade_sigla.value if i.unidade_sigla else "—",
                "Valor unitario": float(i.valor_unitario),
                "Subtotal": round(float(i.quantidade) * float(i.valor_unitario), 2),
            }
            for i in items
        ]
    )


def items_view_column_config() -> dict:
    return {
        "ID produto": st.column_config.NumberColumn("ID produto", format="%d"),
        "Produto": st.column_config.TextColumn("Produto", pinned=True),
        "Quantidade": st.column_config.NumberColumn("Quantidade", format="localized"),
        "Unidade de medida": st.column_config.TextColumn("Unidade"),
        "Valor unitario": st.column_config.NumberColumn("Valor unitário (R$)", format="localized"),
        "Subtotal": st.column_config.NumberColumn("Subtotal (R$)", format="localized"),
    }
