"""DataFrames para a listagem de estoques."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def estoques_df(estoques) -> pd.DataFrame:
    columns = ["ID", "Local de armazenamento"]
    if not estoques:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": e.id_estoque,
                "Local de armazenamento": e.local_descricao or f"#{e.id_local}",
            }
            for e in estoques
        ]
    )


def estoques_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Local de armazenamento": st.column_config.TextColumn("Local de armazenamento", pinned=True),
    }
