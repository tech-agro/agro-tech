"""DataFrame para a listagem de clientes."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.comercial.formatters import STATUS_CLIENTE_LABELS
from components.shared.palette import badge_column, badge_value

_STATUS_OPTIONS = ["Ativo", "Inativo", "Bloqueado"]
_STATUS_TONE = {"Ativo": "green", "Inativo": "gray", "Bloqueado": "red"}


def clientes_df(clientes) -> pd.DataFrame:
    columns = ["ID", "Cliente", "Status"]
    if not clientes:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": c.id_cliente,
                "Cliente": c.pessoa_nome or f"#{c.id_pessoa}",
                "Status": badge_value(STATUS_CLIENTE_LABELS.get(c.status, c.status.value)),
            }
            for c in clientes
        ]
    )


def clientes_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Cliente": st.column_config.TextColumn("Cliente", pinned=True),
        "Status": badge_column("Status", _STATUS_OPTIONS, _STATUS_TONE, width="small"),
    }
