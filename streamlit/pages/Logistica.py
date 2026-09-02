"""Logistica — abas: Operacoes | Cargas | Veiculos | Locais."""

from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from components.logistica import (
    load_dialogs,
    location_dialogs,
    operations_dialogs,
    vehicle_dialogs,
)
from components.logistica.dialog_state import open_dialog
from components.logistica.operation_tables import (
    loads_view_column_config,
    loads_view_df,
    locations_column_config,
    locations_df,
    operations_column_config,
    operations_df,
    vehicles_column_config,
    vehicles_df,
)
from components.shared.screens import (
    crud_toolbar,
    data_table,
    filter_dataframe,
    row_actions,
    setup_page,
    toast_error,
)
from services.logistica_client import LogisticsApiError, LogisticsClient
from services.identity_client import require_login

require_login()

setup_page("Logistica", "Operacoes registram cargas; aba Cargas e consulta.")


def _client() -> LogisticsClient:
    return LogisticsClient()


tab_ops, tab_cargas, tab_veiculos, tab_locais = st.tabs(
    ["Operacoes", "Cargas", "Veiculos", "Locais"]
)


with tab_ops:
    try:
        operations = _client().list_operations()
    except LogisticsApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(key="operacoes")
    if new_clicked:
        open_dialog("operacoes", "create")

    df = filter_dataframe(operations_df(operations), query)
    selected = data_table(df, key="operacoes_grid", column_config=operations_column_config())
    action = row_actions(
        key="operacoes",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    if action == "view" and selected:
        open_dialog("operacoes", "view", int(selected[0]["ID"]))
    elif action == "edit" and selected:
        open_dialog("operacoes", "edit", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("operacoes", "delete", int(selected[0]["ID"]))

    operations_dialogs.render("operacoes")


with tab_cargas:
    st.caption("Consulta das cargas registradas automaticamente pelas operacoes.")
    try:
        loads = _client().list_all_loads()
    except LogisticsApiError as exc:
        toast_error(exc)
        st.stop()

    query = st.text_input(
        "Filtrar",
        placeholder="Filtrar...",
        label_visibility="collapsed",
        key="cargas_filter",
    )
    df = filter_dataframe(loads_view_df(loads), query or "")
    selected = data_table(df, key="cargas_grid", column_config=loads_view_column_config())
    col_info, col_view = st.columns([5, 1])
    with col_info:
        st.caption(f"{len(selected)} de {len(df)} linha(s) selecionada(s).")
    with col_view:
        view_clicked = st.button(
            "Ver",
            icon=":material/visibility:",
            use_container_width=True,
            disabled=not selected,
            key="cargas_view",
        )
    if view_clicked and selected:
        open_dialog("cargas", "view", int(selected[0]["ID"]))

    load_dialogs.render("cargas")


with tab_veiculos:
    try:
        vehicles = _client().list_vehicles()
    except LogisticsApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(key="veiculos")
    if new_clicked:
        open_dialog("veiculos", "create")

    df = filter_dataframe(vehicles_df(vehicles), query)
    selected = data_table(df, key="veiculos_grid", column_config=vehicles_column_config())
    action = row_actions(
        key="veiculos",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    if action == "view" and selected:
        open_dialog("veiculos", "view", int(selected[0]["ID"]))
    elif action == "edit" and selected:
        open_dialog("veiculos", "edit", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("veiculos", "delete", int(selected[0]["ID"]))

    vehicle_dialogs.render("veiculos")


with tab_locais:
    try:
        locations = _client().list_locations()
    except LogisticsApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(key="locais")
    if new_clicked:
        open_dialog("locais", "create")

    df = filter_dataframe(locations_df(locations), query)
    selected = data_table(df, key="locais_grid", column_config=locations_column_config())
    action = row_actions(
        key="locais",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    if action == "view" and selected:
        open_dialog("locais", "view", int(selected[0]["ID"]))
    elif action == "edit" and selected:
        open_dialog("locais", "edit", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("locais", "delete", int(selected[0]["ID"]))

    location_dialogs.render("locais")
