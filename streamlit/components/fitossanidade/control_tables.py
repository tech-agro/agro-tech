"""DataFrames aligned to phytosanitary tables (joins as separate columns)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.fitossanidade.formatters import kind_label
from components.shared.palette import badge_column, badge_value

_SEVERITY_OPTIONS = ["Baixo", "Medio", "Alto", "Critico"]
_SEVERITY_TONE = {"Baixo": "green", "Medio": "orange", "Alto": "orange", "Critico": "red"}


def _blank(value) -> str:
    """Empty cells must render blank — never the literal string 'None'."""
    if value is None:
        return ""
    text = str(value)
    return "" if text in {"None", "nan", "NaT"} else text


def _blank_num(value):
    if value is None:
        return None
    return float(value)


def controls_df(controls) -> pd.DataFrame:
    columns = [
        "ID",
        "ID plantio",
        "Produto",
        "ID funcionario",
        "Funcionario",
        "Identificacao",
        "Severidade",
        "Area afetada (ha)",
        "Recomendacao",
    ]
    if not controls:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": c.id_controle,
                "ID plantio": c.id_plantio,
                "Produto": _blank(c.plantio_produto_nome),
                "ID funcionario": c.id_funcionario,
                "Funcionario": _blank(c.funcionario_nome),
                "Identificacao": c.dt_identificacao,
                "Severidade": badge_value(c.nivel_severidade) if c.nivel_severidade else [],
                "Area afetada (ha)": _blank_num(c.area_afetada_hectares),
                "Recomendacao": _blank(c.recomendacao),
            }
            for c in controls
        ]
    )


def controls_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "ID plantio": st.column_config.NumberColumn("Plantio", format="%d"),
        "Produto": st.column_config.TextColumn("Produto", pinned=True),
        "ID funcionario": None,
        "Funcionario": st.column_config.TextColumn("Funcionário"),
        "Identificacao": st.column_config.DateColumn("Identificação", format="DD/MM/YYYY"),
        "Severidade": badge_column("Severidade", _SEVERITY_OPTIONS, _SEVERITY_TONE, width="small"),
        "Area afetada (ha)": st.column_config.NumberColumn("Área afetada (ha)", format="localized"),
        "Recomendacao": st.column_config.TextColumn("Recomendação", width="large"),
    }


def occurrences_view_df(occurrences) -> pd.DataFrame:
    columns = [
        "ID",
        "ID agente",
        "Agente",
        "Nivel de infestacao",
        "Metodo de controle",
    ]
    if not occurrences:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": o.id_ocorrencia,
                "ID agente": o.id_agente,
                "Agente": _blank(o.agente_nome),
                "Nivel de infestacao": _blank(o.nivel_infestacao),
                "Metodo de controle": _blank(o.metodo_controle),
            }
            for o in occurrences
        ]
    )


def occurrences_view_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "ID agente": None,
        "Agente": st.column_config.TextColumn("Agente", pinned=True),
        "Nivel de infestacao": st.column_config.TextColumn("Nível de infestação"),
        "Metodo de controle": st.column_config.TextColumn("Método de controle"),
    }


def applications_view_df(applications) -> pd.DataFrame:
    columns = [
        "ID",
        "ID insumo",
        "Insumo",
        "ID maquina",
        "Maquina",
        "Dose/ha",
        "Volume aplicado",
        "Data aplicacao",
        "Data carencia",
    ]
    if not applications:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": a.id_aplicacao,
                "ID insumo": a.id_insumo,
                "Insumo": _blank(a.insumo_nome),
                "ID maquina": a.id_maquina,
                "Maquina": _blank(a.maquina_nome),
                "Dose/ha": _blank_num(a.dose_hectare),
                "Volume aplicado": _blank_num(a.volume_aplicado),
                "Data aplicacao": a.dt_aplicacao,
                "Data carencia": a.dt_carencia,
            }
            for a in applications
        ]
    )


def applications_view_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "ID insumo": None,
        "Insumo": st.column_config.TextColumn("Insumo", pinned=True),
        "ID maquina": None,
        "Maquina": st.column_config.TextColumn("Máquina"),
        "Dose/ha": st.column_config.NumberColumn("Dose/ha", format="localized"),
        "Volume aplicado": st.column_config.NumberColumn("Volume aplicado", format="localized"),
        "Data aplicacao": st.column_config.DateColumn("Data da aplicação", format="DD/MM/YYYY"),
        "Data carencia": st.column_config.DateColumn("Data de carência", format="DD/MM/YYYY"),
    }


def agents_df(agents) -> pd.DataFrame:
    columns = [
        "ID",
        "Tipo",
        "Nome comum",
        "Nome cientifico",
        "Tipo praga",
        "Habito alimentar",
        "Agente causador",
        "Sintomas",
        "Condicao favoravel",
    ]
    if not agents:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": a.id_agente,
                "Tipo": kind_label(a.kind),
                "Nome comum": _blank(a.nome_comum),
                "Nome cientifico": _blank(a.nome_cientifico),
                "Tipo praga": _blank(a.tipo_praga),
                "Habito alimentar": _blank(a.habito_alimentar),
                "Agente causador": _blank(a.agente_causador),
                "Sintomas": _blank(a.sintomas),
                "Condicao favoravel": _blank(a.condicao_favoravel),
            }
            for a in agents
        ]
    )


def agents_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Tipo": st.column_config.TextColumn("Tipo", pinned=True),
        "Nome comum": st.column_config.TextColumn("Nome comum", pinned=True),
        "Nome cientifico": st.column_config.TextColumn("Nome científico"),
        "Tipo praga": st.column_config.TextColumn("Tipo de praga"),
        "Habito alimentar": st.column_config.TextColumn("Hábito alimentar"),
        "Agente causador": st.column_config.TextColumn("Agente causador"),
        "Sintomas": st.column_config.TextColumn("Sintomas", width="large"),
        "Condicao favoravel": st.column_config.TextColumn("Condição favorável", width="large"),
    }
