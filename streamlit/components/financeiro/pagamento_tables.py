"""DataFrame para a listagem de pagamentos."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.financeiro.formatters import (
    STATUS_CONTA_OPTIONS,
    STATUS_CONTA_TONE,
    status_conta_label,
)
from components.shared.formatters import format_money_or_dash
from components.shared.palette import badge_column, badge_value


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
                "Valor Pago": float(pagamento.valor_pago),
                "Data Pagamento": pagamento.data_pagamento,
                "Forma Pagamento": pagamento.forma_pagamento or "",
                "Status": badge_value(status_conta_label(pagamento.status)),
                "Saldo": format_money_or_dash(pagamento.saldo),
            }
            for pagamento in pagamentos
        ]
    )


def pagamentos_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Conta": st.column_config.NumberColumn("Conta a pagar", format="%d", pinned=True),
        "Valor Pago": st.column_config.NumberColumn("Valor pago (R$)", format="localized"),
        "Data Pagamento": st.column_config.DateColumn("Data do pagamento", format="DD/MM/YYYY"),
        "Forma Pagamento": st.column_config.TextColumn("Forma de pagamento"),
        "Status": badge_column("Status da conta", STATUS_CONTA_OPTIONS, STATUS_CONTA_TONE, width="small"),
        "Saldo": st.column_config.TextColumn("Saldo restante (R$)", alignment="right"),
    }
