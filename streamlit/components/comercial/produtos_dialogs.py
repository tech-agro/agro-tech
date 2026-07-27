"""Diálogos da entidade Produto."""

from __future__ import annotations

import streamlit as st

from app.comercial.models import NovoProduto
from components.comercial.dialog_state import clear_dialog_state, get_dialog
from services.comercial_client import ComercialApiError, ComercialClient

client = ComercialClient()


def render(scope: str) -> None:
    """Renderiza o diálogo atualmente aberto."""
    dialog = get_dialog(scope)

    if dialog is None:
        return

    kind, entity_id = dialog

    if kind == "create":
        _create_dialog(scope)
    elif entity_id is not None:
        if kind == "view":
            _view_dialog(scope, entity_id)
        elif kind == "delete":
            _delete_dialog(scope, entity_id)


@st.dialog("Novo produto", width="large")
def _create_dialog(scope: str) -> None:
    try:
        categorias = client.list_categorias_produto()
        unidades = client.list_unidades_medida()
    except ComercialApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()
        return

    if not categorias or not unidades:
        st.info("Cadastre ao menos uma categoria e uma unidade de medida antes de criar um produto.")
        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()
        return

    nome = st.text_input("Nome")
    tipo = st.text_input("Tipo (opcional)")
    preco = st.number_input("Preço (opcional)", min_value=0.0, step=0.01, value=0.0)
    categoria = st.selectbox("Categoria", options=categorias, format_func=lambda c: c.nome)
    unidade = st.selectbox("Unidade de medida", options=unidades, format_func=lambda u: f"{u.sigla.value} — {u.descricao}")

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope)
        st.rerun()

    if not salvar:
        return

    if not nome.strip():
        st.error("Informe o nome do produto.")
        return

    payload = NovoProduto(
        id_categoria=categoria.id_categoria,
        id_unidade=unidade.id_unidade,
        nome=nome.strip(),
        tipo=tipo.strip() or None,
        preco=preco,
    )

    try:
        client.create_produto(payload)
    except ComercialApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Produto criado com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes do produto", width="large")
def _view_dialog(scope: str, id_produto: int) -> None:
    try:
        produto = client.get_produto(id_produto)
    except ComercialApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope, id_produto)
            st.rerun()
        return

    st.text_input("Nome", produto.nome, disabled=True)
    st.text_input("Tipo", produto.tipo or "-", disabled=True)
    st.text_input("Preço", f"{produto.preco:.2f}" if produto.preco is not None else "-", disabled=True)

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, id_produto)
        st.rerun()


@st.dialog("Excluir produto")
def _delete_dialog(scope: str, id_produto: int) -> None:
    try:
        produto = client.get_produto(id_produto)
    except ComercialApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope, id_produto)
            st.rerun()
        return

    st.warning(f"Deseja realmente excluir o produto **{produto.nome}**?\n\nEssa ação não poderá ser desfeita.")

    col1, col2 = st.columns(2)
    with col1:
        excluir = st.button("Excluir", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, id_produto)
        st.rerun()

    if not excluir:
        return

    try:
        client.delete_produto(id_produto)
    except ComercialApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope, id_produto)
            st.rerun()
        return

    st.toast("Produto excluído com sucesso.")
    clear_dialog_state(scope, id_produto)
    st.rerun()
