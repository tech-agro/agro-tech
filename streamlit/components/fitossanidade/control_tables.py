"""DataFrames aligned to phytosanitary tables (joins as separate columns)."""

from __future__ import annotations

import pandas as pd

from components.fitossanidade.formatters import kind_label


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
                "Identificacao": (
                    c.dt_identificacao.isoformat() if c.dt_identificacao else ""
                ),
                "Severidade": _blank(c.nivel_severidade),
                "Area afetada (ha)": _blank_num(c.area_afetada_hectares),
                "Recomendacao": _blank(c.recomendacao),
            }
            for c in controls
        ]
    )


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
                "Data aplicacao": a.dt_aplicacao.isoformat() if a.dt_aplicacao else "",
                "Data carencia": a.dt_carencia.isoformat() if a.dt_carencia else "",
            }
            for a in applications
        ]
    )


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
