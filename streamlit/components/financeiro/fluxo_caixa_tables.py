"""DataFrame para a listagem do fluxo de caixa."""

from __future__ import annotations

import pandas as pd

from components.shared.formatters import format_money


def fluxo_caixa_df(fluxos) -> pd.DataFrame:
    columns = [
        "ID",
        "Tipo",
        "Valor",
        "Data Movimento",
        "Origem",
        "Descrição Origem",
        "Conta Pagar",
        "Conta Receber",
        "Pagamento",
        "Recebimento",
    ]

    if not fluxos:
        return pd.DataFrame(columns=columns)

    def _id_label(value) -> str:
        return "" if value is None else str(int(value))

    df = pd.DataFrame(
        [
            {
                "ID": int(fluxo.id_fluxo),
                "Tipo": fluxo.tipo or "",
                "Valor": format_money(float(fluxo.valor)),
                "Data Movimento": (
                    fluxo.data_movimento.strftime("%d/%m/%Y")
                    if fluxo.data_movimento
                    else ""
                ),
                "Origem": fluxo.origem or "",
                "Descrição Origem": fluxo.descricao_origem or "",
                "Conta Pagar": _id_label(fluxo.id_conta_pagar),
                "Conta Receber": _id_label(fluxo.id_conta_receber),
                "Pagamento": _id_label(fluxo.id_pagamento),
                "Recebimento": _id_label(fluxo.id_recebimento),
            }
            for fluxo in fluxos
        ]
    )
    for col in ("Conta Pagar", "Conta Receber", "Pagamento", "Recebimento"):
        df[col] = df[col].astype("string")
    return df