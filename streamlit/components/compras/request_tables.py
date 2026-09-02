"""DataFrames for purchase request lists."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.compras.formatters import (
    PURCHASE_TYPE_LABELS,
    REQUEST_STATUS_OPTIONS,
    REQUEST_STATUS_TONE,
    request_status_label,
)
from components.shared.palette import badge_column, badge_value


def requests_df(requests) -> pd.DataFrame:
    if not requests:
        return pd.DataFrame(
            columns=["ID", "Data", "Tipo", "Status", "Pedido gerado"]
        )
    return pd.DataFrame(
        [
            {
                "ID": r.id_solicitacao,
                "Data": r.data_solicitacao,
                "Tipo": PURCHASE_TYPE_LABELS.get(r.tipo_compra, r.tipo_compra.value),
                "Status": badge_value(request_status_label(r.status)),
                "Pedido gerado": f"#{r.id_pedido}" if r.id_pedido else "—",
            }
            for r in requests
        ]
    )


def requests_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Data": st.column_config.DateColumn("Data da solicitação", format="DD/MM/YYYY"),
        "Tipo": st.column_config.TextColumn("Tipo"),
        "Status": badge_column("Status", REQUEST_STATUS_OPTIONS, REQUEST_STATUS_TONE, width="medium"),
        "Pedido gerado": st.column_config.TextColumn("Pedido gerado"),
    }


def request_items_view_df(items) -> pd.DataFrame:
    columns = ["ID produto", "Produto", "Quantidade", "Unidade de medida"]
    if not items:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID produto": i.id_produto,
                "Produto": i.produto_nome or f"#{i.id_produto}",
                "Quantidade": float(i.quantidade),
                "Unidade de medida": i.unidade_sigla or "—",
            }
            for i in items
        ]
    )


def request_items_view_column_config() -> dict:
    return {
        "ID produto": st.column_config.NumberColumn("ID produto", format="%d"),
        "Produto": st.column_config.TextColumn("Produto", pinned=True),
        "Quantidade": st.column_config.NumberColumn("Quantidade", format="localized"),
        "Unidade de medida": st.column_config.TextColumn("Unidade"),
    }
