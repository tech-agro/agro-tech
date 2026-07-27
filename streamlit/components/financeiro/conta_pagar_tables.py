"""DataFrame para a listagem de contas a pagar."""

from __future__ import annotations

import pandas as pd

from components.shared.formatters import format_money


def contas_pagar_df(contas) -> pd.DataFrame:
    columns = [
        "ID",
        "Origem",
        "Valor",
        "Pago",
        "Saldo",
        "Vencimento",
        "Status",
    ]

    if not contas:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "ID": conta.id_conta_pagar,
                "Origem": conta.origem or "-",
                "Valor": format_money(float(conta.valor)),
                "Pago": format_money(float(conta.valor_pago)),
                "Saldo": format_money(float(conta.saldo)),
                "Vencimento": (
                    conta.vencimento.strftime("%d/%m/%Y")
                    if conta.vencimento
                    else ""
                ),
                "Status": (
                    conta.status.value
                    if conta.status
                    else ""
                ),
            }
            for conta in contas
        ]
    )