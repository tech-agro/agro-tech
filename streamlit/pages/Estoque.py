"""Estoque — abas por entidade: lotes, locais, estoques, certificações,
saldo, movimentações e entradas (recebimento de compra / colheita)."""

from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from components.estoque import (
    certificacoes_dialogs,
    entradas_dialogs,
    estoques_dialogs,
    locais_dialogs,
)
from components.estoque import lotes_dialogs
from components.estoque.dialog_state import open_dialog
from components.estoque.estoques_tables import estoques_df
from components.estoque.formatters import estoque_label
from components.estoque.locais_tables import locais_df
from components.estoque.lotes_tables import lotes_df
from components.estoque.certificacoes_tables import certificacoes_df
from components.estoque.saldos_tables import saldos_df
from components.estoque.movimentacoes_tables import movimentacoes_df
from components.shared.screens import (
    crud_toolbar,
    data_table,
    filter_dataframe,
    row_actions,
    setup_page,
    toast_error,
)
from services.estoque_client import EstoqueApiError, EstoqueClient
from services.identity_client import require_login

require_login()

setup_page("Estoque", "Controle de lotes, armazenagem, saldo e movimentações.")


def _client() -> EstoqueClient:
    return EstoqueClient()


tab_saldo, tab_entradas, tab_mov, tab_estoques, tab_locais, tab_lotes, tab_certificacoes = (
    st.tabs(
        [
            "Saldo",
            "Entradas",
            "Movimentações",
            "Estoques",
            "Locais",
            "Lotes",
            "Certificações",
        ]
    )
)


# ----------------------------------------------------------------------
# Lotes (sem criação avulsa — nasce apenas via Entradas)
# ----------------------------------------------------------------------
with tab_lotes:
    sub_todos, sub_vencendo, sub_vencidos = st.tabs(["Todos", "Vencendo", "Vencidos"])

    def _render_lotes_sub(lotes_loader, key: str) -> None:
        try:
            lotes = lotes_loader()
        except EstoqueApiError as exc:
            toast_error(exc)
            st.stop()

        query = st.text_input(
            "Filtrar",
            placeholder="Filtrar por código, produto...",
            label_visibility="collapsed",
            key=f"{key}_filter",
        )
        df = filter_dataframe(lotes_df(lotes), query)
        selected = data_table(df, key=key)
        action = row_actions(
            key=key,
            selected_count=len(selected),
            total_count=len(df),
            disabled=not selected,
        )

        if action == "view" and selected:
            open_dialog("lotes", "view", int(selected[0]["ID"]))
        elif action == "edit" and selected:
            open_dialog("lotes", "edit", int(selected[0]["ID"]))
        elif action == "delete" and selected:
            open_dialog("lotes", "delete", int(selected[0]["ID"]))

        lotes_dialogs.render("lotes")

    with sub_todos:
        _render_lotes_sub(lambda: _client().list_lotes(limit=500), "lotes_todos")

    with sub_vencendo:
        _render_lotes_sub(
            lambda: _client().list_lotes_proximos_vencimento(dias=30), "lotes_vencendo"
        )

    with sub_vencidos:
        _render_lotes_sub(lambda: _client().list_lotes_vencidos(), "lotes_vencidos")


# ----------------------------------------------------------------------
# Locais de armazenamento
# ----------------------------------------------------------------------
with tab_locais:
    try:
        locais = _client().list_locais()
    except EstoqueApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(
        key="locais",
        filter_placeholder="Filtrar locais...",
        new_label="Novo",
    )
    if new_clicked:
        open_dialog("locais", "create")

    df = filter_dataframe(locais_df(locais), query)
    selected = data_table(df, key="locais_grid")
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

    locais_dialogs.render("locais")


# ----------------------------------------------------------------------
# Estoques
# ----------------------------------------------------------------------
with tab_estoques:
    try:
        estoques = _client().list_estoques()
    except EstoqueApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(
        key="estoques",
        filter_placeholder="Filtrar estoques...",
        new_label="Novo",
    )
    if new_clicked:
        open_dialog("estoques", "create")

    df = filter_dataframe(estoques_df(estoques), query)
    selected = data_table(df, key="estoques_grid")
    action = row_actions(
        key="estoques",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
        show_edit=False
    )

    if action == "view" and selected:
        open_dialog("estoques", "view", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("estoques", "delete", int(selected[0]["ID"]))

    estoques_dialogs.render("estoques")


# ----------------------------------------------------------------------
# Certificações de lote
# ----------------------------------------------------------------------
with tab_certificacoes:
    try:
        certificacoes = _client().list_certificacoes(limit=500)
    except EstoqueApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(
        key="certificacoes",
        filter_placeholder="Filtrar certificações...",
        new_label="Vincular",
    )
    if new_clicked:
        open_dialog("certificacoes", "create")

    df = filter_dataframe(certificacoes_df(certificacoes), query)
    selected = data_table(df, key="certificacoes_grid")
    action = row_actions(
        key="certificacoes",
        selected_count=len(selected),
        total_count=len(df),
        disabled=not selected,
    )

    if action == "view" and selected:
        open_dialog("certificacoes", "view", int(selected[0]["ID"]))
    elif action == "edit" and selected:
        open_dialog("certificacoes", "edit", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("certificacoes", "delete", int(selected[0]["ID"]))

    certificacoes_dialogs.render("certificacoes")


# ----------------------------------------------------------------------
# Saldo (somente consulta)
# ----------------------------------------------------------------------
with tab_saldo:
    try:
        estoque_options = _client().list_estoque_options()
    except EstoqueApiError as exc:
        toast_error(exc)
        st.stop()

    if not estoque_options:
        st.info("Cadastre um estoque para consultar o saldo.")
    else:
        estoque_escolhido = st.selectbox(
            "Estoque",
            options=estoque_options,
            format_func=estoque_label,
            key="saldo_estoque_select",
        )

        try:
            saldos = _client().list_saldo_by_estoque(estoque_escolhido.id_estoque)
        except EstoqueApiError as exc:
            toast_error(exc)
            st.stop()

        st.dataframe(saldos_df(saldos), use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------
# Movimentações (somente consulta)
# ----------------------------------------------------------------------
with tab_mov:
    try:
        estoque_options = _client().list_estoque_options()
    except EstoqueApiError as exc:
        toast_error(exc)
        st.stop()

    if not estoque_options:
        st.info("Cadastre um estoque para consultar as movimentações.")
    else:
        estoque_escolhido = st.selectbox(
            "Estoque",
            options=estoque_options,
            format_func=estoque_label,
            key="mov_estoque_select",
        )

        try:
            movimentacoes = _client().list_movimentacoes_by_estoque(
                estoque_escolhido.id_estoque, limit=100
            )
        except EstoqueApiError as exc:
            toast_error(exc)
            st.stop()

        st.dataframe(
            movimentacoes_df(movimentacoes), use_container_width=True, hide_index=True
        )


# ----------------------------------------------------------------------
# Entradas (recebimento de compra / entrada por colheita)
# ----------------------------------------------------------------------
with tab_entradas:
    st.caption(
        "Registre a entrada de produtos no estoque, seja pelo recebimento "
        "de uma compra ou pela colheita de um produto agrícola."
    )

    col_recebimento, col_colheita = st.columns(2)
    with col_recebimento:
        if st.button(
            "Registrar recebimento de compra",
            type="primary",
            use_container_width=True,
            icon=":material/local_shipping:",
        ):
            open_dialog("entradas", "recebimento")

    with col_colheita:
        if st.button(
            "Registrar entrada por colheita",
            type="primary",
            use_container_width=True,
            icon=":material/agriculture:",
        ):
            open_dialog("entradas", "colheita")

    entradas_dialogs.render("entradas")