"""DataFrames aligned to logistics tables (joins as separate columns)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.logistica.formatters import (
    DISPATCH_STATUS_LABELS,
    OPERATION_STATUS_LABELS,
    location_type_label,
    vehicle_type_label,
)
from components.shared.formatters import format_int_or_dash, format_number_or_dash
from components.shared.palette import badge_column, badge_value

OPERATION_STATUS_OPTIONS = list(OPERATION_STATUS_LABELS.values())
OPERATION_STATUS_TONE = {
    "Aberta": "blue",
    "Em andamento": "orange",
    "Concluida": "green",
    "Cancelada": "gray",
}

_DISPATCH_STATUS_TONE = {
    "Pendente": "gray",
    "Em preparacao": "blue",
    "Expedida": "orange",
    "Entregue": "green",
    "Cancelada": "gray",
}


def operations_df(operations) -> pd.DataFrame:
    columns = [
        "ID",
        "ID veiculo",
        "Placa",
        "ID origem",
        "Origem",
        "ID destino",
        "Destino",
        "ID venda",
        "Cliente",
        "Data inicio",
        "Data fim",
        "Status",
    ]
    if not operations:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": o.id_operacao,
                "ID veiculo": format_int_or_dash(o.id_veiculo),
                "Placa": o.veiculo_placa or "",
                "ID origem": format_int_or_dash(o.id_origem),
                "Origem": o.origem_nome or "",
                "ID destino": format_int_or_dash(o.id_destino),
                "Destino": o.destino_nome or "",
                "ID venda": format_int_or_dash(o.id_venda),
                "Cliente": o.cliente_nome or "",
                "Data inicio": o.data_inicio,
                "Data fim": o.data_fim,
                "Status": badge_value(OPERATION_STATUS_LABELS.get(o.status, o.status.value)),
            }
            for o in operations
        ]
    )


def operations_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "ID veiculo": st.column_config.TextColumn("Veículo", alignment="right"),
        "Placa": st.column_config.TextColumn("Placa", pinned=True),
        "ID origem": st.column_config.TextColumn("ID origem", alignment="right"),
        "Origem": st.column_config.TextColumn("Origem"),
        "ID destino": st.column_config.TextColumn("ID destino", alignment="right"),
        "Destino": st.column_config.TextColumn("Destino"),
        "ID venda": st.column_config.TextColumn("Venda", alignment="right"),
        "Cliente": st.column_config.TextColumn("Cliente"),
        "Data inicio": st.column_config.DatetimeColumn("Início", format="DD/MM/YYYY HH:mm"),
        "Data fim": st.column_config.DatetimeColumn("Fim", format="DD/MM/YYYY HH:mm"),
        "Status": badge_column("Status", OPERATION_STATUS_OPTIONS, OPERATION_STATUS_TONE, width="medium"),
    }


def loads_view_df(loads) -> pd.DataFrame:
    columns = [
        "ID",
        "ID operacao",
        "ID lote",
        "Codigo lote",
        "Produto",
        "Quantidade",
        "Peso previsto",
    ]
    if not loads:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": load.id_carga,
                "ID operacao": load.id_operacao,
                "ID lote": load.id_lote,
                "Codigo lote": load.lote_codigo or "",
                "Produto": load.produto_nome or "",
                "Quantidade": format_number_or_dash(load.quantidade),
                "Peso previsto": format_number_or_dash(load.peso_previsto),
            }
            for load in loads
        ]
    )


def loads_view_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "ID operacao": st.column_config.NumberColumn("Operação", format="%d"),
        "ID lote": st.column_config.NumberColumn("Lote", format="%d"),
        "Codigo lote": st.column_config.TextColumn("Código do lote", pinned=True),
        "Produto": st.column_config.TextColumn("Produto"),
        "Quantidade": st.column_config.TextColumn("Quantidade", alignment="right"),
        "Peso previsto": st.column_config.TextColumn("Peso previsto", alignment="right"),
    }


def weighings_view_df(weighings) -> pd.DataFrame:
    columns = ["ID", "Peso registrado", "Data pesagem"]
    if not weighings:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": w.id_pesagem,
                "Peso registrado": format_number_or_dash(w.peso_registrado),
                "Data pesagem": w.data_pesagem,
            }
            for w in weighings
        ]
    )


def weighings_view_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Peso registrado": st.column_config.TextColumn("Peso registrado", alignment="right"),
        "Data pesagem": st.column_config.DatetimeColumn("Data da pesagem", format="DD/MM/YYYY HH:mm"),
    }


def vehicles_df(vehicles) -> pd.DataFrame:
    columns = ["ID", "Tipo", "Placa", "Capacidade"]
    if not vehicles:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": v.id_veiculo,
                "Tipo": vehicle_type_label(v.tipo),
                "Placa": v.placa,
                "Capacidade": format_number_or_dash(v.capacidade),
            }
            for v in vehicles
        ]
    )


def vehicles_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Tipo": st.column_config.TextColumn("Tipo"),
        "Placa": st.column_config.TextColumn("Placa", pinned=True),
        "Capacidade": st.column_config.TextColumn("Capacidade", alignment="right"),
    }


def locations_df(locations) -> pd.DataFrame:
    columns = [
        "ID",
        "Nome",
        "Tipo",
        "ID endereco",
        "Logradouro",
        "Numero",
        "Cidade",
        "Estado",
        "CEP",
    ]
    if not locations:
        return pd.DataFrame(columns=columns)
    rows = []
    for loc in locations:
        addr = loc.endereco
        rows.append(
            {
                "ID": loc.id_local_logistico,
                "Nome": loc.nome,
                "Tipo": location_type_label(loc.tipo),
                "ID endereco": loc.id_endereco,
                "Logradouro": addr.logradouro if addr else "",
                "Numero": addr.numero if addr else "",
                "Cidade": addr.cidade if addr else "",
                "Estado": addr.estado if addr else "",
                "CEP": addr.cep if addr else "",
            }
        )
    return pd.DataFrame(rows)


def locations_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Nome": st.column_config.TextColumn("Nome", pinned=True),
        "Tipo": st.column_config.TextColumn("Tipo"),
        "ID endereco": None,
        "Logradouro": st.column_config.TextColumn("Logradouro"),
        "Numero": st.column_config.TextColumn("Número"),
        "Cidade": st.column_config.TextColumn("Cidade"),
        "Estado": st.column_config.TextColumn("UF", width="small"),
        "CEP": st.column_config.TextColumn("CEP"),
    }


def dispatch_view_fields(dispatch) -> tuple[str, str]:
    if dispatch is None:
        return ("", "")
    status = DISPATCH_STATUS_LABELS.get(dispatch.status, dispatch.status.value)
    saida = (
        dispatch.data_saida.isoformat(sep=" ", timespec="minutes")
        if dispatch.data_saida
        else ""
    )
    return status, saida
