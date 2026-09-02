"""DataFrame para a listagem de recebimentos."""

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
                "Valor Recebido": float(recebimento.valor_recebido),
                "Data Recebimento": recebimento.data_recebimento,
                "Forma Pagamento": recebimento.forma_pagamento or "",
                "Status": badge_value(status_conta_label(recebimento.status)),
                "Saldo": format_money_or_dash(recebimento.saldo),
            }
            for recebimento in recebimentos
        ]
    )


def recebimentos_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Conta": st.column_config.NumberColumn("Conta a receber", format="%d", pinned=True),
        "Valor Recebido": st.column_config.NumberColumn("Valor recebido (R$)", format="localized"),
        "Data Recebimento": st.column_config.DateColumn("Data do recebimento", format="DD/MM/YYYY"),
        "Forma Pagamento": st.column_config.TextColumn("Forma de pagamento"),
        "Status": badge_column("Status da conta", STATUS_CONTA_OPTIONS, STATUS_CONTA_TONE, width="small"),
        "Saldo": st.column_config.TextColumn("Saldo restante (R$)", alignment="right"),
    }
