"""DataFrames for Manutencao listings."""

from __future__ import annotations

import pandas as pd

from components.manutencao.constants import (
    STATUS_MANUTENCAO_LABELS,
    STATUS_MAQUINA_LABELS,
    STATUS_ORDEM_LABELS,
    status_label,
)


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
                "Status": status_label(m["status"], STATUS_MAQUINA_LABELS),
            }
            for m in maquinas
        ]
    )


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
                "Proxima execucao": p.get("proxima_execucao") or "—",
            }
            for p in planos
        ]
    )


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
                "Status": status_label(
                    item["manutencao"]["status"], STATUS_MANUTENCAO_LABELS
                ),
                "Data execucao": item["manutencao"].get("dt_inicio") or "—",
                "Hodometro": item["preventiva"].get("hodometro_execucao"),
                "Proxima execucao": item.get("proxima_execucao_plano") or "—",
                "Custo": item["manutencao"].get("custo"),
            }
            for item in itens
        ]
    )


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
                "Status": status_label(
                    item["manutencao"]["status"], STATUS_MANUTENCAO_LABELS
                ),
                "Defeito": item["corretiva"].get("defeito_relatado") or "—",
                "Causa raiz": item["corretiva"].get("causa_raiz") or "—",
                "Solucao": item["corretiva"].get("solucao_aplicada") or "—",
                "Data defeito": item["manutencao"].get("dt_inicio") or "—",
                "Custo": item["manutencao"].get("custo"),
            }
            for item in itens
        ]
    )


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
                "Status manutencao": status_label(
                    o.get("status_manutencao"), STATUS_MANUTENCAO_LABELS
                ),
                "Defeito": o.get("defeito_relatado") or "—",
                "Descricao": o.get("descricao") or "—",
                "Status": status_label(o["status"], STATUS_ORDEM_LABELS),
            }
            for o in ordens
        ]
    )
