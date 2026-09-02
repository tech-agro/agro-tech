"""Fitossanidade — abas: Controles | Agentes nocivos."""

from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from components.fitossanidade import agent_dialogs, control_dialogs
from components.fitossanidade.control_tables import agents_column_config, agents_df, controls_column_config, controls_df
from components.fitossanidade.dialog_state import open_dialog
from components.shared.screens import (
    crud_toolbar,
    data_table,
    filter_dataframe,
    row_actions,
    setup_page,
    toast_error,
)
from services.fitossanidade_client import PhytosanitaryApiError, PhytosanitaryClient
from services.identity_client import require_login

require_login()

setup_page(
    "Fitossanidade",
    "Controles fitossanitarios, ocorrencias, aplicacoes e agentes nocivos.",
)


def _client() -> PhytosanitaryClient:
    return PhytosanitaryClient()


tab_controles, tab_agentes = st.tabs(["Controles", "Agentes nocivos"])


with tab_controles:
    try:
        controls = _client().list_controls()
    except PhytosanitaryApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(
        key="controles",
        filter_placeholder="Filtrar controles...",
    )
    if new_clicked:
        open_dialog("controles", "create")

    df = filter_dataframe(controls_df(controls), query)
    selected = data_table(df, key="controles_grid", column_config=controls_column_config())
    action = row_actions(
        key="controles",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    if action == "view" and selected:
        open_dialog("controles", "view", int(selected[0]["ID"]))
    elif action == "edit" and selected:
        open_dialog("controles", "edit", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("controles", "delete", int(selected[0]["ID"]))

    control_dialogs.render("controles")


with tab_agentes:
    try:
        agents = _client().list_agents()
    except PhytosanitaryApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(
        key="agentes",
        filter_placeholder="Filtrar agentes...",
    )
    if new_clicked:
        open_dialog("agentes", "create")

    df = filter_dataframe(agents_df(agents), query)
    selected = data_table(df, key="agentes_grid", column_config=agents_column_config())
    action = row_actions(
        key="agentes",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    if action == "view" and selected:
        open_dialog("agentes", "view", int(selected[0]["ID"]))
    elif action == "edit" and selected:
        open_dialog("agentes", "edit", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("agentes", "delete", int(selected[0]["ID"]))

    agent_dialogs.render("agentes")
