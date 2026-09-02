"""DataFrame para a listagem de produtos."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.shared.formatters import format_money_or_dash


def produtos_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Nome": st.column_config.TextColumn("Nome", pinned=True),
        "Tipo": st.column_config.TextColumn("Tipo"),
        "Preço": st.column_config.TextColumn("Preço (R$)", alignment="right"),
    }


def produtos_df(produtos) -> pd.DataFrame:
    columns = ["ID", "Nome", "Tipo", "Preço"]
    if not produtos:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": p.id_produto,
                "Nome": p.nome,
                "Tipo": p.tipo or "",
                "Preço": format_money_or_dash(p.preco),
            }
            for p in produtos
        ]
    )
