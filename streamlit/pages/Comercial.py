"""Comercial — vendas, clientes, produtos e catálogo."""

from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from components.comercial import catalogo_dialogs, clientes_dialogs, produtos_dialogs, vendas_dialogs
from components.comercial.catalogo_tables import categorias_df, centros_custo_df, certificacoes_df, unidades_df
from components.comercial.clientes_tables import clientes_df
from components.comercial.dialog_state import open_dialog
from components.comercial.formatters import cliente_label
from components.comercial.produtos_tables import produtos_df
from components.comercial.vendas_tables import vendas_df
from components.shared.screens import (
    crud_toolbar,
    data_table,
    filter_dataframe,
    row_actions,
    setup_page,
    toast_error,
)
from services.comercial_client import ComercialApiError, ComercialClient
from services.financeiro_client import FinanceiroApiError, FinanceiroClient
from services.identity_client import require_login

require_login()

setup_page("Comercial", "Vendas, clientes, produtos e catálogo comercial.")


def _client() -> ComercialClient:
    return ComercialClient()


def _financeiro_client() -> FinanceiroClient:
    return FinanceiroClient()


tab_vendas, tab_clientes, tab_produtos, tab_catalogo = st.tabs(
    ["Vendas", "Clientes", "Produtos", "Catálogo"]
)


# ----------------------------------------------------------------------
# Vendas (sem edição avulsa — nasce completa via "Nova venda")
# ----------------------------------------------------------------------
with tab_vendas:
    try:
        vendas = _client().list_vendas()
        clientes_opt = _client().list_cliente_options()
    except ComercialApiError as exc:
        toast_error(exc)
        st.stop()

    cliente_por_id = {c.id_cliente: cliente_label(c) for c in clientes_opt}

    try:
        contas_receber = _financeiro_client().list_contas_receber(limit=500)
        conta_por_venda = {c.id_venda: c for c in contas_receber if c.id_venda is not None}
    except FinanceiroApiError:
        conta_por_venda = {}
        st.caption("⚠ Nao foi possivel carregar o status de recebimento do Financeiro agora.")

    if vendas:
        total_valor = sum(float(v.valor_total) for v in vendas)
        total_a_receber = sum(
            float(c.saldo) for c in conta_por_venda.values() if c.saldo
        )
        vencidas = sum(1 for c in conta_por_venda.values() if c.status == "VENCIDA")
        c1, c2, c3 = st.columns(3)
        c1.metric("Vendas", len(vendas))
        c2.metric("Total vendido", f"R$ {total_valor:,.2f}")
        c3.metric("A receber (com vencidas)", f"R$ {total_a_receber:,.2f}", delta=f"{vencidas} vencida(s)" if vencidas else None, delta_color="inverse")
        st.divider()

    query, new_clicked = crud_toolbar(key="vendas", filter_placeholder="Filtrar vendas...", new_label="Nova venda")
    if new_clicked:
        open_dialog("vendas", "create")

    df = filter_dataframe(vendas_df(vendas, cliente_por_id, conta_por_venda), query)
    selected = data_table(df, key="vendas_grid")
    action = row_actions(key="vendas", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False)

    if action == "view" and selected:
        open_dialog("vendas", "view", int(selected[0]["ID"]))

    vendas_dialogs.render("vendas")


# ----------------------------------------------------------------------
# Clientes
# ----------------------------------------------------------------------
with tab_clientes:
    try:
        clientes = _client().list_clientes()
    except ComercialApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(key="clientes", filter_placeholder="Filtrar clientes...", new_label="Novo")
    if new_clicked:
        open_dialog("clientes", "create")

    df = filter_dataframe(clientes_df(clientes), query)
    selected = data_table(df, key="clientes_grid")
    action = row_actions(key="clientes", selected_count=len(selected), total_count=len(df), disabled=not selected)

    if action == "view" and selected:
        open_dialog("clientes", "view", int(selected[0]["ID"]))
    elif action == "edit" and selected:
        open_dialog("clientes", "edit", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("clientes", "delete", int(selected[0]["ID"]))

    clientes_dialogs.render("clientes")


# ----------------------------------------------------------------------
# Produtos
# ----------------------------------------------------------------------
with tab_produtos:
    try:
        produtos = _client().list_produtos()
    except ComercialApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(key="produtos", filter_placeholder="Filtrar produtos...", new_label="Novo")
    if new_clicked:
        open_dialog("produtos", "create")

    df = filter_dataframe(produtos_df(produtos), query)
    selected = data_table(df, key="produtos_grid")
    action = row_actions(key="produtos", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False)

    if action == "view" and selected:
        open_dialog("produtos", "view", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("produtos", "delete", int(selected[0]["ID"]))

    produtos_dialogs.render("produtos")


# ----------------------------------------------------------------------
# Catálogo (categorias, unidades de medida, certificações)
# ----------------------------------------------------------------------
with tab_catalogo:
    sub_categorias, sub_unidades, sub_certificacoes, sub_centros_custo = st.tabs(
        ["Categorias", "Unidades de medida", "Certificações", "Centros de custo"]
    )

    with sub_categorias:
        try:
            categorias = _client().list_categorias_produto()
        except ComercialApiError as exc:
            toast_error(exc)
            st.stop()

        query, new_clicked = crud_toolbar(key="categorias", filter_placeholder="Filtrar categorias...", new_label="Nova")
        if new_clicked:
            open_dialog("categorias", "create")

        df = filter_dataframe(categorias_df(categorias), query)
        selected = data_table(df, key="categorias_grid")
        action = row_actions(key="categorias", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False)

        if action == "delete" and selected:
            open_dialog("categorias", "delete", int(selected[0]["ID"]))

        catalogo_dialogs.render("categorias")

    with sub_unidades:
        try:
            unidades = _client().list_unidades_medida()
        except ComercialApiError as exc:
            toast_error(exc)
            st.stop()

        query, new_clicked = crud_toolbar(key="unidades", filter_placeholder="Filtrar unidades...", new_label="Nova")
        if new_clicked:
            open_dialog("unidades", "create")

        df = filter_dataframe(unidades_df(unidades), query)
        selected = data_table(df, key="unidades_grid")
        action = row_actions(key="unidades", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False)

        if action == "delete" and selected:
            open_dialog("unidades", "delete", int(selected[0]["ID"]))

        catalogo_dialogs.render("unidades")

    with sub_certificacoes:
        try:
            certificacoes = _client().list_certificacoes()
        except ComercialApiError as exc:
            toast_error(exc)
            st.stop()

        query, new_clicked = crud_toolbar(
            key="certificacoes_comercial", filter_placeholder="Filtrar certificações...", new_label="Nova"
        )
        if new_clicked:
            open_dialog("certificacoes", "create")

        df = filter_dataframe(certificacoes_df(certificacoes), query)
        selected = data_table(df, key="certificacoes_comercial_grid")
        action = row_actions(
            key="certificacoes_comercial", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False
        )

        if action == "delete" and selected:
            open_dialog("certificacoes", "delete", int(selected[0]["ID"]))

        catalogo_dialogs.render("certificacoes")

    with sub_centros_custo:
        try:
            centros_custo = _client().list_centro_custo_options()
        except ComercialApiError as exc:
            toast_error(exc)
            st.stop()

        query, new_clicked = crud_toolbar(
            key="centros_custo", filter_placeholder="Filtrar centros de custo...", new_label="Novo"
        )
        if new_clicked:
            open_dialog("centros_custo", "create")

        df = filter_dataframe(centros_custo_df(centros_custo), query)
        selected = data_table(df, key="centros_custo_grid")
        action = row_actions(
            key="centros_custo", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False
        )

        if action == "delete" and selected:
            open_dialog("centros_custo", "delete", int(selected[0]["ID"]))

        catalogo_dialogs.render("centros_custo")
