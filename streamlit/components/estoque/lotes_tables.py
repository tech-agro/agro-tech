"""DataFrame para a listagem de lotes."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.shared.palette import badge_column, badge_value

_STATUS_LABELS = {"EM_ANALISE": "Em análise", "LIBERADO": "Liberado", "BLOQUEADO": "Bloqueado"}
_STATUS_OPTIONS = ["Em análise", "Liberado", "Bloqueado"]
_STATUS_TONE = {"Em análise": "blue", "Liberado": "green", "Bloqueado": "red"}


def lotes_df(lotes) -> pd.DataFrame:
    columns = ["ID", "Código", "Produto", "Validade", "Qualidade", "Status"]
    if not lotes:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": l.id_lote,
                "Código": l.codigo_lote,
                "Produto": l.produto_nome or f"#{l.id_produto}",
                "Validade": l.validade,
                "Qualidade": l.qualidade or "",
                "Status": badge_value(_STATUS_LABELS.get(l.status.value, l.status.value)),
            }
            for l in lotes
        ]
    )


def lotes_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Código": st.column_config.TextColumn("Código", pinned=True),
        "Produto": st.column_config.TextColumn("Produto"),
        "Validade": st.column_config.DateColumn("Validade", format="DD/MM/YYYY"),
        "Qualidade": st.column_config.TextColumn("Qualidade"),
        "Status": badge_column("Status", _STATUS_OPTIONS, _STATUS_TONE, width="small"),
    }
