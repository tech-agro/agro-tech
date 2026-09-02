"""Visao geral de estoque: ocupacao por local (vs capacidade) e onde cada lote esta."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.bi.widgets import fmt_qty


def render_ocupacao_locais(ocupacoes: list) -> None:
    if not ocupacoes:
        st.info("Nenhum local de armazenamento cadastrado.")
        return

    with st.container(horizontal=True):
        for local in ocupacoes:
            ocupado = float(local.ocupado)
            capacidade = float(local.capacidade) if local.capacidade is not None else None

            with st.container(border=True):
                st.markdown(f"**{local.descricao}**")
                if capacidade and capacidade > 0:
                    fracao = min(ocupado / capacidade, 1.0)
                    pct = fracao * 100
                    st.progress(fracao)
                    if pct >= 90:
                        st.caption(f":red[{fmt_qty(ocupado)} / {fmt_qty(capacidade)} ({pct:.0f}%) — quase lotado]")
                    else:
                        st.caption(f"{fmt_qty(ocupado)} / {fmt_qty(capacidade)} ({pct:.0f}%)")
                else:
                    st.caption("Sem capacidade cadastrada")
                    st.caption(f"{fmt_qty(ocupado)} em estoque")


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


def localizacao_lotes_column_config() -> dict:
    return {
        "Lote": st.column_config.TextColumn("Lote", pinned=True),
        "Produto": st.column_config.TextColumn("Produto"),
        "Local": st.column_config.TextColumn("Local"),
        "Quantidade": st.column_config.NumberColumn("Quantidade", format="localized"),
        "Reservada": st.column_config.NumberColumn("Reservada", format="localized"),
    }
