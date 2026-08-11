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

    return pd.DataFrame(
        [
            {
                "ID": fluxo.id_fluxo,
                "Tipo": fluxo.tipo or "",
                "Valor": format_money(
                    float(fluxo.valor)
                ),
                "Data Movimento": (
                    fluxo.data_movimento.strftime("%d/%m/%Y")
                    if fluxo.data_movimento
                    else ""
                ),
                "Origem": fluxo.origem or "",
                "Descrição Origem": fluxo.descricao_origem or "",
                "Conta Pagar": (
                    str(fluxo.id_conta_pagar)
                    if fluxo.id_conta_pagar is not None
                    else ""
                ),
                "Conta Receber": (
                    str(fluxo.id_conta_receber)
                    if fluxo.id_conta_receber is not None
                    else ""
                ),
                "Pagamento": (
                    str(fluxo.id_pagamento)
                    if fluxo.id_pagamento is not None
                    else ""
                ),
                "Recebimento": (
                    str(fluxo.id_recebimento)
                    if fluxo.id_recebimento is not None
                    else ""
                ),
            }
            for fluxo in fluxos
        ]
    )