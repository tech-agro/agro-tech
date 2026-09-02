"""DataFrame para a listagem de saldos de estoque."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def saldos_df(saldos) -> pd.DataFrame:
    columns = ["ID", "Produto", "Quantidade atual"]
    if not saldos:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": s.id_saldo,
                "Produto": s.produto_nome or f"#{s.id_produto}",
                "Quantidade atual": float(s.quantidade_atual),
            }
            for s in saldos
        ]
    )


def saldos_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Produto": st.column_config.TextColumn("Produto", pinned=True),
        "Quantidade atual": st.column_config.NumberColumn("Quantidade atual", format="localized"),
    }
