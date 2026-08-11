"""Dialogs for machines (maquinas)."""

from __future__ import annotations

import streamlit as st

from components.manutencao.constants import (
    STATUS_MAQUINA,
    STATUS_MAQUINA_LABELS,
    status_from_label,
    status_label,
    status_options,
)
from components.manutencao.dialog_state import clear_dialog_state, get_dialog
from components.manutencao.lookups import select_fazenda, select_tipo_maquina
from components.shared.screens import toast_ok
import services.manutencao_client as api
from services import producao_client as producao_api

SCOPE = "maquinas"


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


def _load_fazendas() -> list[dict]:
    try:
        return producao_api.listar("/fazendas")
    except Exception as exc:
        st.error(f"Nao foi possivel carregar fazendas: {exc}")
        return []


def _load_tipos() -> list[dict]:
    try:
        return api.list_tipos_maquina()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar tipos de maquina: {exc}")
        return []


def _find_maquina(maquina_id: int) -> dict | None:
    try:
        maquinas = api.list_maquinas()
    except Exception:
        return None
    for maquina in maquinas:
        if int(maquina["id_maquina"]) == int(maquina_id):
            return maquina
    return None


@st.dialog("Nova maquina", width="large")
def _create_dialog(scope: str) -> None:
    fazendas = _load_fazendas()
    tipos = _load_tipos()

    id_fazenda = select_fazenda(
        "Fazenda",
        fazendas,
        key=f"_nova_maquina_fazenda_{scope}",
    )
    id_tipo_maquina = select_tipo_maquina(
        "Tipo",
        tipos,
        key=f"_nova_maquina_tipo_{scope}",
    )
    nome = st.text_input("Nome", key=f"_nova_maquina_nome_{scope}")
    maquina_status_options = status_options(STATUS_MAQUINA, STATUS_MAQUINA_LABELS)
    status_choice = st.selectbox(
        "Status",
        maquina_status_options,
        key=f"_nova_maquina_status_{scope}",
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

    if id_fazenda is None:
        st.error("Selecione uma fazenda.")
        return
    if id_tipo_maquina is None:
        st.error("Selecione um tipo de maquina.")
        return
    if not nome.strip():
        st.error("Informe o nome da maquina.")
        return

    try:
        api.create_maquina(
            {
                "id_fazenda": int(id_fazenda),
                "id_tipo_maquina": int(id_tipo_maquina),
                "nome": nome.strip(),
                "status": status_from_label(
                    status_choice, STATUS_MAQUINA, STATUS_MAQUINA_LABELS
                ),
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Maquina cadastrada.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes da maquina", width="large")
def _view_dialog(scope: str, maquina_id: int) -> None:
    maquina = _find_maquina(maquina_id)
    if maquina is None:
        st.error("Maquina nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, maquina_id)
            st.rerun()
        return

    st.text_input("ID", value=str(maquina["id_maquina"]), disabled=True)
    st.text_input("Nome", value=maquina["nome"], disabled=True)
    st.text_input("Fazenda", value=maquina.get("nome_fazenda") or "—", disabled=True)
    st.text_input("Tipo", value=maquina.get("descricao_tipo") or "—", disabled=True)
    st.text_input(
        "Status",
        value=status_label(maquina["status"], STATUS_MAQUINA_LABELS),
        disabled=True,
    )

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, maquina_id)
        st.rerun()


@st.dialog("Editar maquina", width="large")
def _edit_dialog(scope: str, maquina_id: int) -> None:
    maquina = _find_maquina(maquina_id)
    if maquina is None:
        st.error("Maquina nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, maquina_id)
            st.rerun()
        return

    tipos = _load_tipos()
    st.caption(f"Fazenda: {maquina.get('nome_fazenda') or '—'}")

    id_tipo_maquina = select_tipo_maquina(
        "Tipo",
        tipos,
        key=f"_edit_maquina_tipo_{scope}_{maquina_id}",
        id_atual=int(maquina["id_tipo_maquina"]),
    )
    nome = st.text_input(
        "Nome",
        value=maquina["nome"],
        key=f"_edit_maquina_nome_{scope}_{maquina_id}",
    )
    maquina_status_options = status_options(STATUS_MAQUINA, STATUS_MAQUINA_LABELS)
    status_index = (
        STATUS_MAQUINA.index(maquina["status"])
        if maquina["status"] in STATUS_MAQUINA
        else 0
    )
    status_choice = st.selectbox(
        "Status",
        maquina_status_options,
        index=status_index,
        key=f"_edit_maquina_status_{scope}_{maquina_id}",
    )

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, maquina_id)
        st.rerun()

    if not salvar:
        return

    if id_tipo_maquina is None:
        st.error("Selecione um tipo de maquina.")
        return
    if not nome.strip():
        st.error("Informe o nome da maquina.")
        return

    try:
        api.update_maquina(
            maquina_id,
            {
                "id_tipo_maquina": int(id_tipo_maquina),
                "nome": nome.strip(),
                "status": status_from_label(
                    status_choice, STATUS_MAQUINA, STATUS_MAQUINA_LABELS
                ),
            },
        )
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Maquina atualizada.")
    clear_dialog_state(scope, maquina_id)
    st.rerun()


@st.dialog("Excluir maquina")
def _delete_dialog(scope: str, maquina_id: int) -> None:
    maquina = _find_maquina(maquina_id)
    if maquina is None:
        st.error("Maquina nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, maquina_id)
            st.rerun()
        return

    st.warning(
        f"Deseja realmente excluir a maquina **{maquina['nome']}**?\n\n"
        "Essa acao nao podera ser desfeita."
    )

    col1, col2 = st.columns(2)
    with col1:
        excluir = st.button("Excluir", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, maquina_id)
        st.rerun()

    if not excluir:
        return

    try:
        api.delete_maquina(maquina_id)
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Maquina excluida.")
    clear_dialog_state(scope, maquina_id)
    st.rerun()
