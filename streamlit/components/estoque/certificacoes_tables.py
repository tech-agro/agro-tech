"""DataFrame para a listagem de certificações de lote."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.estoque.formatters import STATUS_LABELS
from components.shared.palette import badge_column, badge_value

_STATUS_OPTIONS = list(STATUS_LABELS.values())
_STATUS_TONE = {"Vigente": "green", "Vencida": "red", "Suspensa": "orange", "Cancelada": "gray"}


def certificacoes_df(certificacoes) -> pd.DataFrame:
    columns = ["ID", "Certificação", "Lote", "Emissão", "Validade", "Número", "Status"]
    if not certificacoes:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": c.id_cert_lote,
                "Certificação": c.certificacao_nome or f"#{c.id_certificacao}",
                "Lote": c.lote_codigo or f"#{c.id_lote}",
                "Emissão": c.dt_emissao,
                "Validade": c.dt_validade,
                "Número": c.numero_certificado or "",
                "Status": badge_value(STATUS_LABELS.get(c.status, c.status.value)),
            }
            for c in certificacoes
        ]
    )


def certificacoes_column_config() -> dict:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d", pinned=True, width="small"),
        "Certificação": st.column_config.TextColumn("Certificação", pinned=True),
        "Lote": st.column_config.TextColumn("Lote"),
        "Emissão": st.column_config.DateColumn("Emissão", format="DD/MM/YYYY"),
        "Validade": st.column_config.DateColumn("Validade", format="DD/MM/YYYY"),
        "Número": st.column_config.TextColumn("Número"),
        "Status": badge_column("Status", _STATUS_OPTIONS, _STATUS_TONE, width="small"),
    }
