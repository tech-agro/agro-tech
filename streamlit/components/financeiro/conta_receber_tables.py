"""Tabelas de exibição para contas a receber."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.financeiro.schemas import ContaReceberReadSchema
from components.financeiro.formatters import (
    STATUS_CONTA_OPTIONS,
    STATUS_CONTA_TONE,
    status_conta_label,
)
from components.shared.palette import badge_column, badge_value


def contas_receber_dataframe(
    contas: list[ContaReceberReadSchema],
) -> pd.DataFrame:
    """Converte contas a receber para tabela Streamlit."""

    columns = [
        "ID",
        "Venda",
        "Valor",
        "Recebido",
        "% recebido",
        "Saldo",
        "Vencimento",
        "Status",
    ]

    if not contas:
        return pd.DataFrame(columns=columns)

    linhas = []
    for conta in contas:
        valor = float(conta.valor)
        recebido = float(conta.valor_recebido)
        linhas.append(
            {
                "ID": conta.id_conta_receber,
                "Venda": conta.id_venda,
                "Valor": valor,
                "Recebido": recebido,
                "% recebido": round(100 * recebido / valor, 1) if valor else 0.0,
                "Saldo": float(conta.saldo),
                "Vencimento": conta.vencimento,
                "Status": badge_value(status_conta_label(conta.status)),
            }
        )
    return pd.DataFrame(linhas, columns=columns)


def contas_receber_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Venda": st.column_config.NumberColumn("Venda", format="%d"),
        "Valor": st.column_config.NumberColumn("Valor (R$)", format="localized"),
        "Recebido": st.column_config.NumberColumn("Recebido (R$)", format="localized"),
        "% recebido": st.column_config.ProgressColumn("% recebido", format="%.0f%%", min_value=0, max_value=100),
        "Saldo": st.column_config.NumberColumn("Saldo (R$)", format="localized"),
        "Vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
        "Status": badge_column("Status", STATUS_CONTA_OPTIONS, STATUS_CONTA_TONE, width="small"),
    }
