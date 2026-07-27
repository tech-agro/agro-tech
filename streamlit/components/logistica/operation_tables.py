"""DataFrames aligned to logistics tables (joins as separate columns)."""

from __future__ import annotations

import pandas as pd

from components.logistica.formatters import (
    DISPATCH_STATUS_LABELS,
    OPERATION_STATUS_LABELS,
    location_type_label,
    vehicle_type_label,
)


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
                "ID veiculo": o.id_veiculo,
                "Placa": o.veiculo_placa or "",
                "ID origem": o.id_origem,
                "Origem": o.origem_nome or "",
                "ID destino": o.id_destino,
                "Destino": o.destino_nome or "",
                "ID venda": o.id_venda,
                "Cliente": o.cliente_nome or "",
                "Data inicio": o.data_inicio.isoformat(sep=" ", timespec="minutes")
                if o.data_inicio
                else "",
                "Data fim": o.data_fim.isoformat(sep=" ", timespec="minutes")
                if o.data_fim
                else "",
                "Status": OPERATION_STATUS_LABELS.get(o.status, o.status.value),
            }
            for o in operations
        ]
    )


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
                "Quantidade": float(load.quantidade)
                if load.quantidade is not None
                else None,
                "Peso previsto": float(load.peso_previsto)
                if load.peso_previsto is not None
                else None,
            }
            for load in loads
        ]
    )


def weighings_view_df(weighings) -> pd.DataFrame:
    columns = ["ID", "Peso registrado", "Data pesagem"]
    if not weighings:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": w.id_pesagem,
                "Peso registrado": float(w.peso_registrado)
                if w.peso_registrado is not None
                else None,
                "Data pesagem": w.data_pesagem.isoformat(sep=" ", timespec="minutes")
                if w.data_pesagem
                else "",
            }
            for w in weighings
        ]
    )


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
                "Capacidade": float(v.capacidade) if v.capacidade is not None else None,
            }
            for v in vehicles
        ]
    )


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
