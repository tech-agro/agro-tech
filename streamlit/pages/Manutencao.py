"""Manutencao — abas: Tipos | Maquinas | Prestadores | Planos | Preventiva | Corretiva | OS."""

from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from components.manutencao import (
    corretiva_dialogs,
    maquinas_dialogs,
    ordens_dialogs,
    planos_dialogs,
    prestadores_dialogs,
    preventiva_dialogs,
    tipos_dialogs,
)
from components.manutencao.dialog_state import open_dialog
from components.manutencao.tables import (
    corretivas_column_config,
    corretivas_df,
    maquinas_column_config,
    maquinas_df,
    ordens_column_config,
    ordens_df,
    planos_column_config,
    planos_df,
    prestadores_column_config,
    prestadores_df,
    preventivas_column_config,
    preventivas_df,
    tipos_column_config,
    tipos_df,
)
from components.shared.screens import (
    crud_toolbar,
    data_table,
    filter_dataframe,
    row_actions,
    setup_page,
    toast_error,
)
from services import manutencao_client as api
from services.identity_client import require_login

require_login()

setup_page(
    "Manutencao",
    "Gestao de maquinas, planos, prestadores e manutencoes.",
)


def _handle_crud_actions(
    *,
    scope: str,
    selected: list[dict],
    action: str | None,
) -> None:
    if not action or not selected:
        return
    entity_id = int(selected[0]["ID"])
    if action == "view":
        open_dialog(scope, "view", entity_id)
    elif action == "edit":
        open_dialog(scope, "edit", entity_id)
    elif action == "delete":
        open_dialog(scope, "delete", entity_id)


(
    tab_tipos,
    tab_maquinas,
    tab_prestadores,
    tab_planos,
    tab_preventiva,
    tab_corretiva,
    tab_ordens,
) = st.tabs(
    [
        "Tipos de maquina",
        "Maquinas",
        "Prestadores",
        "Planos de manutencao",
        "Manutencao preventiva",
        "Manutencao corretiva",
        "Ordens de servico",
    ]
)


with tab_tipos:
    try:
        tipos = api.list_tipos_maquina()
    except Exception as exc:
        toast_error(exc)
        tipos = []

    query, new_clicked = crud_toolbar(
        key="manut_tipos",
        filter_placeholder="Filtrar tipos...",
    )
    if new_clicked:
        open_dialog("tipos", "create")

    df = filter_dataframe(tipos_df(tipos), query)
    selected = data_table(df, key="manut_tipos", column_config=tipos_column_config())
    action = row_actions(
        key="manut_tipos",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    _handle_crud_actions(scope="tipos", selected=selected, action=action)
    tipos_dialogs.render("tipos")


with tab_maquinas:
    try:
        maquinas = api.list_maquinas()
    except Exception as exc:
        toast_error(exc)
        maquinas = []

    query, new_clicked = crud_toolbar(
        key="manut_maquinas",
        filter_placeholder="Filtrar maquinas...",
    )
    if new_clicked:
        open_dialog("maquinas", "create")

    df = filter_dataframe(maquinas_df(maquinas), query)
    selected = data_table(df, key="manut_maquinas", column_config=maquinas_column_config())
    action = row_actions(
        key="manut_maquinas",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    _handle_crud_actions(scope="maquinas", selected=selected, action=action)
    maquinas_dialogs.render("maquinas")


with tab_prestadores:
    try:
        prestadores = api.list_prestadores()
    except Exception as exc:
        toast_error(exc)
        prestadores = []

    query, new_clicked = crud_toolbar(
        key="manut_prestadores",
        filter_placeholder="Filtrar prestadores...",
    )
    if new_clicked:
        open_dialog("prestadores", "create")

    df = filter_dataframe(prestadores_df(prestadores), query)
    selected = data_table(df, key="manut_prestadores", column_config=prestadores_column_config())
    action = row_actions(
        key="manut_prestadores",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    _handle_crud_actions(scope="prestadores", selected=selected, action=action)
    prestadores_dialogs.render("prestadores")


with tab_planos:
    try:
        planos = api.list_planos_manutencao()
    except Exception as exc:
        toast_error(exc)
        planos = []

    query, new_clicked = crud_toolbar(
        key="manut_planos",
        filter_placeholder="Filtrar planos...",
    )
    if new_clicked:
        open_dialog("planos", "create")

    df = filter_dataframe(planos_df(planos), query)
    selected = data_table(df, key="manut_planos", column_config=planos_column_config())
    action = row_actions(
        key="manut_planos",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    _handle_crud_actions(scope="planos", selected=selected, action=action)
    planos_dialogs.render("planos")


with tab_preventiva:
    try:
        preventivas = api.list_manutencoes_preventivas()
    except Exception as exc:
        toast_error(exc)
        preventivas = []

    query, new_clicked = crud_toolbar(
        key="manut_preventivas",
        filter_placeholder="Filtrar preventivas...",
    )
    if new_clicked:
        open_dialog("preventivas", "create")

    df = filter_dataframe(preventivas_df(preventivas), query)
    selected = data_table(df, key="manut_preventivas", column_config=preventivas_column_config())
    action = row_actions(
        key="manut_preventivas",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    _handle_crud_actions(scope="preventivas", selected=selected, action=action)
    preventiva_dialogs.render("preventivas")


with tab_corretiva:
    try:
        corretivas = api.list_manutencoes_corretivas()
    except Exception as exc:
        toast_error(exc)
        corretivas = []

    query, new_clicked = crud_toolbar(
        key="manut_corretivas",
        filter_placeholder="Filtrar corretivas...",
    )
    if new_clicked:
        open_dialog("corretivas", "create")

    df = filter_dataframe(corretivas_df(corretivas), query)
    selected = data_table(df, key="manut_corretivas", column_config=corretivas_column_config())
    action = row_actions(
        key="manut_corretivas",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    _handle_crud_actions(scope="corretivas", selected=selected, action=action)
    corretiva_dialogs.render("corretivas")


with tab_ordens:
    try:
        ordens = api.list_ordens_servico()
    except Exception as exc:
        toast_error(exc)
        ordens = []

    query, new_clicked = crud_toolbar(
        key="manut_ordens",
        filter_placeholder="Filtrar ordens...",
    )
    if new_clicked:
        open_dialog("ordens", "create")

    df = filter_dataframe(ordens_df(ordens), query)
    selected = data_table(df, key="manut_ordens", column_config=ordens_column_config())
    action = row_actions(
        key="manut_ordens",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )
    _handle_crud_actions(scope="ordens", selected=selected, action=action)
    ordens_dialogs.render("ordens")
