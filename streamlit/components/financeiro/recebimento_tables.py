"""DataFrame para a listagem de recebimentos."""

from __future__ import annotations

import pandas as pd

from components.shared.formatters import format_money


def recebimentos_df(recebimentos) -> pd.DataFrame:
    columns = [
        "ID",
        "Conta",
        "Valor Recebido",
        "Data Recebimento",
        "Forma Pagamento",
        "Status",
        "Saldo",
    ]

    if not recebimentos:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "ID": recebimento.id_recebimento,
                "Conta": recebimento.id_conta_receber,
                "Valor Recebido": format_money(
                    float(recebimento.valor_recebido)
                ),
                "Data Recebimento": (
                    recebimento.data_recebimento.strftime("%d/%m/%Y")
                    if recebimento.data_recebimento
                    else ""
                ),
                "Forma Pagamento": recebimento.forma_pagamento or "",
                "Status": (
                    recebimento.status.value
                    if recebimento.status
                    else ""
                ),
                "Saldo": (
                    format_money(float(recebimento.saldo))
                    if recebimento.saldo is not None
                    else ""
                ),
            }
            for recebimento in recebimentos
        ]
    )