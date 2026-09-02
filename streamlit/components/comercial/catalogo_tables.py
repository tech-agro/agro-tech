"""DataFrames para a listagem de categorias, unidades de medida e certificações."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def _id_pinned(label: str = "ID") -> dict:
    return {label: st.column_config.NumberColumn(label, format="%d", pinned=True, width="small")}


def categorias_df(categorias) -> pd.DataFrame:
    columns = ["ID", "Nome"]
    if not categorias:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame([{"ID": c.id_categoria, "Nome": c.nome} for c in categorias])


def categorias_column_config() -> dict:
    return _id_pinned()


def centros_custo_df(centros_custo) -> pd.DataFrame:
    columns = ["ID", "Nome"]
    if not centros_custo:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame([{"ID": c.id_centro_custo, "Nome": c.nome} for c in centros_custo])


def centros_custo_column_config() -> dict:
    return _id_pinned()


def unidades_df(unidades) -> pd.DataFrame:
    columns = ["ID", "Sigla", "Descrição"]
    if not unidades:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [{"ID": u.id_unidade, "Sigla": u.sigla.value, "Descrição": u.descricao} for u in unidades]
    )


def unidades_column_config() -> dict:
    return _id_pinned()


def certificacoes_df(certificacoes) -> pd.DataFrame:
    columns = ["ID", "Nome", "Órgão emissor", "Tipo"]
    if not certificacoes:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": c.id_certificacao,
                "Nome": c.nome,
                "Órgão emissor": c.orgao_emissor or "",
                "Tipo": c.tipo or "",
            }
            for c in certificacoes
        ]
    )


def certificacoes_column_config() -> dict:
    return _id_pinned()
