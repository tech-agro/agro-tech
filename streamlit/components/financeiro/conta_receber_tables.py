"""Tabelas de exibição para contas a receber."""

from __future__ import annotations

import pandas as pd

from app.financeiro.schemas import ContaReceberReadSchema
from components.shared.formatters import format_money


def contas_receber_dataframe(
    contas: list[ContaReceberReadSchema],
) -> pd.DataFrame:
    """Converte contas a receber para tabela Streamlit."""

    columns = [
        "ID",
        "Venda",
        "Valor",
        "Recebido",
        "Saldo",
        "Vencimento",
        "Status",
    ]

    if not contas:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "ID": conta.id_conta_receber,
                "Venda": conta.id_venda,
                "Valor": format_money(float(conta.valor)),
                "Recebido": format_money(float(conta.valor_recebido)),
                "Saldo": format_money(float(conta.saldo)),
                "Vencimento": (
                    conta.vencimento.strftime("%d/%m/%Y")
                    if conta.vencimento
                    else ""
                ),
                "Status": conta.status.value if conta.status else "",
            }
            for conta in contas
        ],
        columns=columns,
    )
