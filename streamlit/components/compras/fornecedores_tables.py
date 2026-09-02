"""DataFrame for the suppliers listing."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def fornecedores_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Nome": st.column_config.TextColumn("Nome", pinned=True),
        "Documento": st.column_config.TextColumn("Documento"),
        "Categoria": st.column_config.TextColumn("Categoria"),
    }


def fornecedores_df(suppliers) -> pd.DataFrame:
    columns = ["ID", "Nome", "Documento", "Categoria"]
    if not suppliers:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": s.id_fornecedor,
                "Nome": s.nome,
                "Documento": s.documento,
                "Categoria": s.categoria or "—",
            }
            for s in suppliers
        ]
    )
