"""DataFrames for Manutencao listings."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.manutencao.constants import (
    STATUS_MANUTENCAO_LABELS,
    STATUS_MAQUINA_LABELS,
    STATUS_ORDEM_LABELS,
    status_label,
)
from components.shared.palette import badge_column, badge_value

_MAQUINA_OPTIONS = list(STATUS_MAQUINA_LABELS.values())
_MAQUINA_TONE = {
    "Disponivel": "green",
    "Em uso": "blue",
    "Em manutencao": "orange",
    "Inativa": "gray",
}

_MANUTENCAO_OPTIONS = list(STATUS_MANUTENCAO_LABELS.values())
_MANUTENCAO_TONE = {
    "Aberta": "blue",
    "Em execucao": "orange",
    "Concluida": "green",
    "Cancelada": "gray",
}

_ORDEM_OPTIONS = list(STATUS_ORDEM_LABELS.values())
_ORDEM_TONE = {
    "Aberta": "blue",
    "Em execucao": "orange",
    "Concluida": "green",
    "Cancelada": "gray",
}


def _as_date(value):
    if value is None or value == "—":
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed


def tipos_df(tipos: list[dict]) -> pd.DataFrame:
    columns = ["ID", "Descricao"]
    if not tipos:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {"ID": t["id_tipo_maquina"], "Descricao": t["descricao"]}
            for t in tipos
        ]
    )


def tipos_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Descricao": st.column_config.TextColumn("Descrição", pinned=True),
    }


def maquinas_df(maquinas: list[dict]) -> pd.DataFrame:
    columns = ["ID", "Nome", "Fazenda", "Tipo", "Status"]
    if not maquinas:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": m["id_maquina"],
                "Nome": m["nome"],
                "Fazenda": m.get("nome_fazenda") or "—",
                "Tipo": m.get("descricao_tipo") or "—",
                "Status": badge_value(status_label(m["status"], STATUS_MAQUINA_LABELS)),
            }
            for m in maquinas
        ]
    )


def maquinas_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Nome": st.column_config.TextColumn("Nome", pinned=True),
        "Fazenda": st.column_config.TextColumn("Fazenda"),
        "Tipo": st.column_config.TextColumn("Tipo"),
        "Status": badge_column("Status", _MAQUINA_OPTIONS, _MAQUINA_TONE, width="medium"),
    }


def prestadores_df(prestadores: list[dict]) -> pd.DataFrame:
    columns = ["ID", "Nome", "CNPJ", "Especialidade", "Telefone"]
    if not prestadores:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": p["id_prestador"],
                "Nome": p["nome"],
                "CNPJ": p["cnpj"],
                "Especialidade": p["especialidade"],
                "Telefone": p["telefone"],
            }
            for p in prestadores
        ]
    )


def prestadores_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Nome": st.column_config.TextColumn("Nome", pinned=True),
        "CNPJ": st.column_config.TextColumn("CNPJ"),
        "Especialidade": st.column_config.TextColumn("Especialidade"),
        "Telefone": st.column_config.TextColumn("Telefone"),
    }


def planos_df(planos: list[dict]) -> pd.DataFrame:
    columns = ["ID", "Maquina", "Periodicidade", "Proxima execucao"]
    if not planos:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": p["id_plano"],
                "Maquina": p.get("nome_maquina") or "—",
                "Periodicidade": p.get("periodicidade") or "—",
                "Proxima execucao": _as_date(p.get("proxima_execucao")),
            }
            for p in planos
        ]
    )


def planos_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Maquina": st.column_config.TextColumn("Máquina", pinned=True),
        "Periodicidade": st.column_config.TextColumn("Periodicidade"),
        "Proxima execucao": st.column_config.DateColumn("Próxima execução", format="DD/MM/YYYY"),
    }


def preventivas_df(itens: list[dict]) -> pd.DataFrame:
    columns = [
        "ID",
        "Plano",
        "Maquina",
        "Periodicidade",
        "Status",
        "Data execucao",
        "Hodometro",
        "Proxima execucao",
        "Custo",
    ]
    if not itens:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": item["manutencao"]["id_manutencao"],
                "Plano": item["preventiva"]["id_plano"],
                "Maquina": item.get("nome_maquina") or "—",
                "Periodicidade": item.get("periodicidade") or "—",
                "Status": badge_value(
                    status_label(item["manutencao"]["status"], STATUS_MANUTENCAO_LABELS)
                ),
                "Data execucao": _as_date(item["manutencao"].get("dt_inicio")),
                "Hodometro": item["preventiva"].get("hodometro_execucao"),
                "Proxima execucao": _as_date(item.get("proxima_execucao_plano")),
                "Custo": item["manutencao"].get("custo"),
            }
            for item in itens
        ]
    )


def preventivas_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Plano": st.column_config.NumberColumn("Plano", format="%d"),
        "Maquina": st.column_config.TextColumn("Máquina", pinned=True),
        "Periodicidade": st.column_config.TextColumn("Periodicidade"),
        "Status": badge_column("Status", _MANUTENCAO_OPTIONS, _MANUTENCAO_TONE, width="medium"),
        "Data execucao": st.column_config.DateColumn("Data de execução", format="DD/MM/YYYY"),
        "Hodometro": st.column_config.NumberColumn("Hodômetro", format="localized"),
        "Proxima execucao": st.column_config.DateColumn("Próxima execução", format="DD/MM/YYYY"),
        "Custo": st.column_config.NumberColumn("Custo (R$)", format="localized"),
    }


def corretivas_df(itens: list[dict]) -> pd.DataFrame:
    columns = [
        "ID",
        "Maquina",
        "Status",
        "Defeito",
        "Causa raiz",
        "Solucao",
        "Data defeito",
        "Custo",
    ]
    if not itens:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": item["manutencao"]["id_manutencao"],
                "Maquina": item.get("nome_maquina") or "—",
                "Status": badge_value(
                    status_label(item["manutencao"]["status"], STATUS_MANUTENCAO_LABELS)
                ),
                "Defeito": item["corretiva"].get("defeito_relatado") or "—",
                "Causa raiz": item["corretiva"].get("causa_raiz") or "—",
                "Solucao": item["corretiva"].get("solucao_aplicada") or "—",
                "Data defeito": _as_date(item["manutencao"].get("dt_inicio")),
                "Custo": item["manutencao"].get("custo"),
            }
            for item in itens
        ]
    )


def corretivas_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Maquina": st.column_config.TextColumn("Máquina", pinned=True),
        "Status": badge_column("Status", _MANUTENCAO_OPTIONS, _MANUTENCAO_TONE, width="medium"),
        "Defeito": st.column_config.TextColumn("Defeito", width="large"),
        "Causa raiz": st.column_config.TextColumn("Causa raiz", width="large"),
        "Solucao": st.column_config.TextColumn("Solução", width="large"),
        "Data defeito": st.column_config.DateColumn("Data do defeito", format="DD/MM/YYYY"),
        "Custo": st.column_config.NumberColumn("Custo (R$)", format="localized"),
    }


def ordens_df(ordens: list[dict]) -> pd.DataFrame:
    columns = [
        "ID",
        "Manutencao",
        "Maquina",
        "Tipo",
        "Status manutencao",
        "Defeito",
        "Descricao",
        "Status",
    ]
    if not ordens:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": o["id_ordem_servico"],
                "Manutencao": o["id_manutencao"],
                "Maquina": o.get("nome_maquina") or "—",
                "Tipo": o.get("tipo_manutencao") or "—",
                "Status manutencao": badge_value(
                    status_label(o.get("status_manutencao"), STATUS_MANUTENCAO_LABELS)
                ),
                "Defeito": o.get("defeito_relatado") or "—",
                "Descricao": o.get("descricao") or "—",
                "Status": badge_value(status_label(o["status"], STATUS_ORDEM_LABELS)),
            }
            for o in ordens
        ]
    )


def ordens_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Manutencao": st.column_config.NumberColumn("Manutenção", format="%d"),
        "Maquina": st.column_config.TextColumn("Máquina", pinned=True),
        "Tipo": st.column_config.TextColumn("Tipo"),
        "Status manutencao": badge_column("Status manutenção", _MANUTENCAO_OPTIONS, _MANUTENCAO_TONE, width="medium"),
        "Defeito": st.column_config.TextColumn("Defeito", width="large"),
        "Descricao": st.column_config.TextColumn("Descrição", width="large"),
        "Status": badge_column("Status", _ORDEM_OPTIONS, _ORDEM_TONE, width="medium"),
    }
