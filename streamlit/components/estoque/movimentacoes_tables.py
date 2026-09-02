"""DataFrame para a listagem de movimentações de estoque."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.shared.palette import badge_column, badge_value

_TIPO_LABELS: dict[str, str] = {
    "entrada_compra": "Entrada (compra)",
    "entrada_colheita": "Entrada (colheita)",
    "saida_venda": "Saída (venda)",
    "saida_atividade": "Saída (atividade)",
}
_TIPO_OPTIONS = list(_TIPO_LABELS.values())
_TIPO_TONE = {
    "Entrada (compra)": "green",
    "Entrada (colheita)": "green",
    "Saída (venda)": "red",
    "Saída (atividade)": "red",
}


def movimentacoes_df(movimentacoes) -> pd.DataFrame:
    columns = ["ID", "Produto", "Lote", "Tipo", "Quantidade", "Data"]
    if not movimentacoes:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": m.id_movimentacao,
                "Produto": m.produto_nome or f"#{m.id_produto}",
                "Lote": m.lote_codigo or "-",
                "Tipo": badge_value(_TIPO_LABELS.get(m.tipo_movimentacao, m.tipo_movimentacao)),
                "Quantidade": float(m.quantidade),
                "Data": m.data_movimentacao,
            }
            for m in movimentacoes
        ]
    )


def movimentacoes_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Produto": st.column_config.TextColumn("Produto", pinned=True),
        "Lote": st.column_config.TextColumn("Lote"),
        "Tipo": badge_column("Tipo", _TIPO_OPTIONS, _TIPO_TONE, width="medium"),
        "Quantidade": st.column_config.NumberColumn("Quantidade", format="localized"),
        "Data": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
    }
