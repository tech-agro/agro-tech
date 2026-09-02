"""DataFrame para a listagem do fluxo de caixa."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.shared.formatters import format_int_or_dash
from components.shared.palette import badge_column, badge_value

_TIPO_LABEL = {"ENTRADA": "Entrada", "SAIDA": "Saída"}
_TIPO_OPTIONS = ["Entrada", "Saída"]
_TIPO_TONE = {"Entrada": "green", "Saída": "red"}


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
                "ID": int(fluxo.id_fluxo),
                "Tipo": badge_value(_TIPO_LABEL.get(fluxo.tipo, fluxo.tipo or "—")),
                "Valor": float(fluxo.valor),
                "Data Movimento": fluxo.data_movimento,
                "Origem": fluxo.origem or "",
                "Descrição Origem": fluxo.descricao_origem or "",
                "Conta Pagar": format_int_or_dash(fluxo.id_conta_pagar),
                "Conta Receber": format_int_or_dash(fluxo.id_conta_receber),
                "Pagamento": format_int_or_dash(fluxo.id_pagamento),
                "Recebimento": format_int_or_dash(fluxo.id_recebimento),
            }
            for fluxo in fluxos
        ]
    )


def fluxo_caixa_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Tipo": badge_column("Tipo", _TIPO_OPTIONS, _TIPO_TONE, width="small"),
        "Valor": st.column_config.NumberColumn("Valor (R$)", format="localized"),
        "Data Movimento": st.column_config.DateColumn("Data do movimento", format="DD/MM/YYYY"),
        "Origem": st.column_config.TextColumn("Origem"),
        "Descrição Origem": st.column_config.TextColumn("Descrição"),
        "Conta Pagar": st.column_config.TextColumn("Conta a pagar", alignment="right"),
        "Conta Receber": st.column_config.TextColumn("Conta a receber", alignment="right"),
        "Pagamento": st.column_config.TextColumn("Pagamento", alignment="right"),
        "Recebimento": st.column_config.TextColumn("Recebimento", alignment="right"),
    }
