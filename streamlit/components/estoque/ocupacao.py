"""Visao geral de estoque: ocupacao por local (vs capacidade) e onde cada lote esta."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_ocupacao_locais(ocupacoes: list) -> None:
    if not ocupacoes:
        st.info("Nenhum local de armazenamento cadastrado.")
        return

    for local in ocupacoes:
        ocupado = float(local.ocupado)
        capacidade = float(local.capacidade) if local.capacidade is not None else None

        col_nome, col_barra, col_valor = st.columns([2, 4, 2])
        with col_nome:
            st.markdown(f"**{local.descricao}**")
        with col_barra:
            if capacidade and capacidade > 0:
                fracao = min(ocupado / capacidade, 1.0)
                st.progress(fracao)
            else:
                st.caption("Sem capacidade cadastrada")
        with col_valor:
            if capacidade and capacidade > 0:
                pct = (ocupado / capacidade) * 100
                st.caption(f"{ocupado:,.0f} / {capacidade:,.0f} ({pct:.0f}%)")
            else:
                st.caption(f"{ocupado:,.0f} em estoque")


def localizacao_lotes_df(localizacoes: list) -> pd.DataFrame:
    columns = ["Lote", "Produto", "Local", "Quantidade", "Reservada"]
    if not localizacoes:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "Lote": item.codigo_lote,
                "Produto": item.produto_nome or "-",
                "Local": item.local_descricao,
                "Quantidade": float(item.quantidade_atual),
                "Reservada": float(item.quantidade_reservada),
            }
            for item in localizacoes
        ]
    )
