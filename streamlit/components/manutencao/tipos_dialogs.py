"""Dialogs for machine types (tipos de maquina)."""

from __future__ import annotations

import streamlit as st

from components.manutencao.dialog_state import clear_dialog_state, get_dialog
from components.shared.screens import toast_ok
import services.manutencao_client as api

SCOPE = "tipos"


def render(scope: str = SCOPE) -> None:
    dialog = get_dialog(scope)
    if dialog is None:
        return

    kind, entity_id = dialog
    if kind == "create":
        _create_dialog(scope)
    elif entity_id is not None:
        if kind == "view":
            _view_dialog(scope, entity_id)
        elif kind == "edit":
            _edit_dialog(scope, entity_id)
        elif kind == "delete":
            _delete_dialog(scope, entity_id)


def _find_tipo(tipo_id: int) -> dict | None:
    try:
        return api.get_tipo_maquina(tipo_id)
    except Exception:
        return None


@st.dialog("Novo tipo de maquina", width="large")
def _create_dialog(scope: str) -> None:
    descricao = st.text_input(
        "Descricao",
        placeholder="Trator, Colheitadeira...",
        key=f"_novo_tipo_descricao_{scope}",
    )

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
        st.error("Informe a descricao do tipo.")
        return

    try:
        api.create_tipo_maquina({"descricao": descricao.strip()})
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Tipo de maquina cadastrado.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes do tipo de maquina", width="large")
def _view_dialog(scope: str, tipo_id: int) -> None:
    tipo = _find_tipo(tipo_id)
    if tipo is None:
        st.error("Tipo de maquina nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, tipo_id)
            st.rerun()
        return

    st.text_input("ID", value=str(tipo["id_tipo_maquina"]), disabled=True)
    st.text_input("Descricao", value=tipo["descricao"], disabled=True)

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, tipo_id)
        st.rerun()


@st.dialog("Editar tipo de maquina", width="large")
def _edit_dialog(scope: str, tipo_id: int) -> None:
    tipo = _find_tipo(tipo_id)
    if tipo is None:
        st.error("Tipo de maquina nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, tipo_id)
            st.rerun()
        return

    descricao = st.text_input(
        "Descricao",
        value=tipo["descricao"],
        key=f"_edit_tipo_descricao_{scope}_{tipo_id}",
    )

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, tipo_id)
        st.rerun()

    if not salvar:
        return

    if not descricao.strip():
        st.error("Informe a descricao do tipo.")
        return

    try:
        api.update_tipo_maquina(tipo_id, {"descricao": descricao.strip()})
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Tipo de maquina atualizado.")
    clear_dialog_state(scope, tipo_id)
    st.rerun()


@st.dialog("Excluir tipo de maquina")
def _delete_dialog(scope: str, tipo_id: int) -> None:
    tipo = _find_tipo(tipo_id)
    if tipo is None:
        st.error("Tipo de maquina nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, tipo_id)
            st.rerun()
        return

    st.warning(
        f"Deseja realmente excluir o tipo **{tipo['descricao']}**?\n\n"
        "Essa acao nao podera ser desfeita."
    )

    col1, col2 = st.columns(2)
    with col1:
        excluir = st.button("Excluir", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, tipo_id)
        st.rerun()

    if not excluir:
        return

    try:
        api.delete_tipo_maquina(tipo_id)
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Tipo de maquina excluido.")
    clear_dialog_state(scope, tipo_id)
    st.rerun()
