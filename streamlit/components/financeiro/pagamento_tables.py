"""DataFrame para a listagem de pagamentos."""

from __future__ import annotations

import pandas as pd

from components.shared.formatters import format_money


def pagamentos_df(pagamentos) -> pd.DataFrame:
    columns = [
        "ID",
        "Conta",
        "Valor Pago",
        "Data Pagamento",
        "Forma Pagamento",
        "Status",
        "Saldo",
    ]

    if not pagamentos:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "ID": pagamento.id_pagamento,
                "Conta": pagamento.id_conta_pagar,
                "Valor Pago": format_money(
                    float(pagamento.valor_pago)
                ),
                "Data Pagamento": (
                    pagamento.data_pagamento.strftime("%d/%m/%Y")
                    if pagamento.data_pagamento
                    else ""
                ),
                "Forma Pagamento": pagamento.forma_pagamento or "",
                "Status": (
                    pagamento.status.value
                    if pagamento.status
                    else ""
                ),
                "Saldo": (
                    format_money(float(pagamento.saldo))
                    if pagamento.saldo is not None
                    else ""
                ),
            }
            for pagamento in pagamentos
        ]
    )