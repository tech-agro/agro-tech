"""DataFrame para a listagem de contas a pagar."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.financeiro.formatters import (
    STATUS_CONTA_OPTIONS,
    STATUS_CONTA_TONE,
    status_conta_label,
)
from components.shared.palette import badge_column, badge_value


def contas_pagar_df(contas) -> pd.DataFrame:
    columns = [
        "ID",
        "Origem",
        "Valor",
        "Pago",
        "% pago",
        "Saldo",
        "Vencimento",
        "Status",
    ]

    if not contas:
        return pd.DataFrame(columns=columns)

    linhas = []
    for conta in contas:
        valor = float(conta.valor)
        pago = float(conta.valor_pago)
        linhas.append(
            {
                "ID": conta.id_conta_pagar,
                "Origem": conta.origem or "-",
                "Valor": valor,
                "Pago": pago,
                "% pago": round(100 * pago / valor, 1) if valor else 0.0,
                "Saldo": float(conta.saldo),
                "Vencimento": conta.vencimento,
                "Status": badge_value(status_conta_label(conta.status)),
            }
        )
    return pd.DataFrame(linhas)


def contas_pagar_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Origem": st.column_config.TextColumn("Origem", pinned=True),
        "Valor": st.column_config.NumberColumn("Valor (R$)", format="localized"),
        "Pago": st.column_config.NumberColumn("Pago (R$)", format="localized"),
        "% pago": st.column_config.ProgressColumn("% pago", format="%.0f%%", min_value=0, max_value=100),
        "Saldo": st.column_config.NumberColumn("Saldo (R$)", format="localized"),
        "Vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
        "Status": badge_column("Status", STATUS_CONTA_OPTIONS, STATUS_CONTA_TONE, width="small"),
    }
