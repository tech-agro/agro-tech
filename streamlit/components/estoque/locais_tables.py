"""DataFrame para a listagem de locais de armazenamento."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.shared.formatters import format_number_or_dash


def locais_df(locais) -> pd.DataFrame:
    columns = ["ID", "Descrição", "Capacidade"]
    if not locais:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": local.id_local,
                "Descrição": local.descricao,
                "Capacidade": format_number_or_dash(local.capacidade),
            }
            for local in locais
        ]
    )


def locais_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Descrição": st.column_config.TextColumn("Descrição", pinned=True),
        "Capacidade": st.column_config.TextColumn("Capacidade", alignment="right"),
    }
