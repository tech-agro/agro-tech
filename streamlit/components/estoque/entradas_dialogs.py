"""Diálogos de entrada de estoque (recebimento de compra e colheita)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import streamlit as st

from app.estoque.schemas.entrada_colheita_estoque import EntradaColheitaCreateSchema
from app.estoque.schemas.recebimento_compra import RecebimentoCompraCreateSchema
from components.estoque.dialog_state import clear_dialog_state, get_dialog
from components.estoque.formatters import (
    colheita_label,
    estoque_label,
    item_pedido_label,
    produto_label,
)
from services.estoque_client import EstoqueApiError, EstoqueClient


client = EstoqueClient()


def render(scope: str) -> None:
    """Renderiza o diálogo atualmente aberto."""
    dialog = get_dialog(scope)

    if dialog is None:
        return

    kind, _entity_id = dialog

    if kind == "recebimento":
        _recebimento_dialog(scope)

    elif kind == "colheita":
        _colheita_dialog(scope)


@st.dialog("Registrar recebimento de compra", width="large")
def _recebimento_dialog(scope: str) -> None:
    try:
        itens_pedido = client.list_item_pedido_options()
        estoques = client.list_estoque_options()

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    if not itens_pedido:
        st.info(
            "Nenhum item de pedido pendente de recebimento. "
            "Aprove um pedido de compra antes de registrar o recebimento."
        )

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    if not estoques:
        st.info("Cadastre um estoque antes de registrar um recebimento.")

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    item_pedido = st.selectbox(
        "Item do pedido",
        options=itens_pedido,
        format_func=item_pedido_label,
    )

    estoque = st.selectbox(
        "Estoque de destino",
        options=estoques,
        format_func=estoque_label,
    )

    quantidade_recebida = st.number_input(
        "Quantidade recebida",
        min_value=0.01,
        step=1.0,
        format="%.2f",
    )

    data_recebimento = st.date_input("Data do recebimento", value=None)

    st.caption(
        "Informe o código do lote se o produto vier identificado pelo fornecedor "
        "(nota fiscal ou etiqueta). Se não houver, deixe em branco."
    )
    codigo_lote = st.text_input("Código do lote (opcional)")
    validade_lote = st.date_input("Validade do lote (opcional)", value=None)

    col1, col2 = st.columns(2)

    with col1:
        salvar = st.button("Registrar", use_container_width=True)

    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope)
        st.rerun()

    if not salvar:
        return

    payload = RecebimentoCompraCreateSchema(
        id_item_pedido=item_pedido.id_item_pedido,
        id_estoque=estoque.id_estoque,
        quantidade_recebida=Decimal(str(quantidade_recebida)),
        data_recebimento=(
            datetime.combine(data_recebimento, datetime.min.time())
            if data_recebimento
            else None
        ),
        codigo_lote=codigo_lote.strip() or None,
        validade_lote=validade_lote,
    )

    try:
        client.registrar_recebimento(payload)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    st.toast("Recebimento registrado com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Registrar entrada por colheita", width="large")
def _colheita_dialog(scope: str) -> None:
    try:
        colheitas = client.list_colheita_options()
        produtos = client.list_produto_options()
        estoques = client.list_estoque_options()

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    if not colheitas:
        st.info("Nenhuma colheita disponível para registrar entrada.")

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    if not produtos:
        st.info("Cadastre um produto antes de registrar a entrada.")

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    if not estoques:
        st.info("Cadastre um estoque antes de registrar a entrada.")

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    colheita = st.selectbox(
        "Colheita",
        options=colheitas,
        format_func=colheita_label,
    )

    produto = st.selectbox(
        "Produto colhido",
        options=produtos,
        format_func=produto_label,
    )

    estoque = st.selectbox(
        "Estoque de destino",
        options=estoques,
        format_func=estoque_label,
    )

    quantidade = st.number_input(
        "Quantidade colhida",
        min_value=0.01,
        step=1.0,
        format="%.2f",
    )

    codigo_lote = st.text_input("Código do lote")

    col_val, col_qual = st.columns(2)
    with col_val:
        validade_lote = st.date_input("Validade (opcional)", value=None)
    with col_qual:
        qualidade_lote = st.text_input("Qualidade (opcional)")

    data_entrada = st.date_input("Data da entrada", value=None)

    col1, col2 = st.columns(2)

    with col1:
        salvar = st.button("Registrar", use_container_width=True)

    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope)
        st.rerun()

    if not salvar:
        return

    if not codigo_lote.strip():
        st.error("Informe o código do lote.")
        return

    payload = EntradaColheitaCreateSchema(
        id_colheita=colheita.id_colheita,
        id_produto=produto.id_produto,
        id_estoque=estoque.id_estoque,
        quantidade=Decimal(str(quantidade)),
        codigo_lote=codigo_lote.strip(),
        validade_lote=validade_lote,
        qualidade_lote=qualidade_lote.strip() or None,
        data_entrada=(
            datetime.combine(data_entrada, datetime.min.time())
            if data_entrada
            else None
        ),
    )

    try:
        client.registrar_entrada_colheita(payload)

    except EstoqueApiError as exc:
        st.error(exc.user_message)

        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()

        return

    st.toast("Entrada por colheita registrada com sucesso.")
    clear_dialog_state(scope)
    st.rerun()