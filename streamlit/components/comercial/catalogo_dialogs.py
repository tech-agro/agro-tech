"""Diálogos de criação/exclusão do catálogo (categorias, unidades, certificações)."""

from __future__ import annotations

import streamlit as st

from app.comercial.enum import UnitSymbol
from app.comercial.models import NovaCategoriaProduto, NovaCertificacao, NovaUnidadeMedida, NovoCentroCusto
from components.comercial.dialog_state import clear_dialog_state, get_dialog
from services.comercial_client import ComercialApiError, ComercialClient

client = ComercialClient()


def render(scope: str) -> None:
    """Renderiza o diálogo atualmente aberto. `scope` e um de:
    'categorias', 'unidades', 'certificacoes', 'centros_custo'."""
    dialog = get_dialog(scope)

    if dialog is None:
        return

    kind, entity_id = dialog

    if kind == "create":
        if scope == "categorias":
            _create_categoria(scope)
        elif scope == "unidades":
            _create_unidade(scope)
        elif scope == "certificacoes":
            _create_certificacao(scope)
        elif scope == "centros_custo":
            _create_centro_custo(scope)
    elif kind == "delete" and entity_id is not None:
        _delete_dialog(scope, entity_id)


@st.dialog("Nova categoria", width="large")
def _create_categoria(scope: str) -> None:
    nome = st.text_input("Nome")

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
        st.error("Informe o nome da categoria.")
        return

    try:
        client.create_categoria_produto(NovaCategoriaProduto(nome=nome.strip()))
    except ComercialApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Categoria criada com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Nova unidade de medida", width="large")
def _create_unidade(scope: str) -> None:
    sigla = st.selectbox("Sigla", options=list(UnitSymbol), format_func=lambda s: s.value)
    descricao = st.text_input("Descrição")

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

    if not descricao.strip():
        st.error("Informe a descrição da unidade.")
        return

    try:
        client.create_unidade_medida(NovaUnidadeMedida(sigla=sigla, descricao=descricao.strip()))
    except ComercialApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Unidade de medida criada com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Nova certificação", width="large")
def _create_certificacao(scope: str) -> None:
    nome = st.text_input("Nome")
    orgao_emissor = st.text_input("Órgão emissor (opcional)")
    tipo = st.text_input("Tipo (opcional)")

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
        st.error("Informe o nome da certificação.")
        return

    try:
        client.create_certificacao(
            NovaCertificacao(nome=nome.strip(), orgao_emissor=orgao_emissor.strip() or None, tipo=tipo.strip() or None)
        )
    except ComercialApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Certificação criada com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Novo centro de custo", width="large")
def _create_centro_custo(scope: str) -> None:
    nome = st.text_input("Nome")

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
        st.error("Informe o nome do centro de custo.")
        return

    try:
        client.create_centro_custo(NovoCentroCusto(nome=nome.strip()))
    except ComercialApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Centro de custo criado com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


_DELETE_FN = {
    "categorias": lambda id_: client.delete_categoria_produto(id_),
    "unidades": lambda id_: client.delete_unidade_medida(id_),
    "certificacoes": lambda id_: client.delete_certificacao(id_),
    "centros_custo": lambda id_: client.delete_centro_custo(id_),
}

_DELETE_LABEL = {
    "categorias": "a categoria",
    "unidades": "a unidade de medida",
    "certificacoes": "a certificação",
    "centros_custo": "o centro de custo",
}


@st.dialog("Excluir registro")
def _delete_dialog(scope: str, entity_id: int) -> None:
    st.warning(f"Deseja realmente excluir {_DELETE_LABEL.get(scope, 'o registro')} selecionado(a)?\n\nEssa ação não poderá ser desfeita.")

    col1, col2 = st.columns(2)
    with col1:
        excluir = st.button("Excluir", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, entity_id)
        st.rerun()

    if not excluir:
        return

    try:
        _DELETE_FN[scope](entity_id)
    except ComercialApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope, entity_id)
            st.rerun()
        return

    st.toast("Registro excluído com sucesso.")
    clear_dialog_state(scope, entity_id)
    st.rerun()
