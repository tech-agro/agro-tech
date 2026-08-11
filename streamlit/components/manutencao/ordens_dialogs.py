"""Dialogs for service orders (ordens de servico)."""

from __future__ import annotations

import streamlit as st

from components.manutencao.constants import (
    STATUS_MANUTENCAO_LABELS,
    STATUS_ORDEM,
    STATUS_ORDEM_LABELS,
    status_from_label,
    status_label,
    status_options,
)
from components.manutencao.dialog_state import clear_dialog_state, get_dialog
from components.manutencao.lookups import select_manutencao_corretiva
from components.shared.screens import toast_ok
import services.manutencao_client as api

SCOPE = "ordens"


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


def _find_ordem(ordem_id: int) -> dict | None:
    try:
        ordens = api.list_ordens_servico()
    except Exception:
        return None
    for ordem in ordens:
        if int(ordem["id_ordem_servico"]) == int(ordem_id):
            return ordem
    return None


def _load_corretivas() -> list[dict]:
    try:
        return api.list_manutencoes_corretivas()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar manutencoes: {exc}")
        return []


@st.dialog("Nova ordem de servico", width="large")
def _create_dialog(scope: str) -> None:
    manutencoes = _load_corretivas()

    id_manutencao = select_manutencao_corretiva(
        "Manutencao corretiva",
        manutencoes,
        key=f"_nova_os_manutencao_{scope}",
        apenas_abertas=True,
    )
    descricao = st.text_area("Descricao", key=f"_nova_os_descricao_{scope}")

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

    if id_manutencao is None:
        st.error("Selecione uma manutencao.")
        return

    try:
        api.create_ordem_servico(
            {
                "id_manutencao": int(id_manutencao),
                "descricao": descricao.strip() or None,
                "status": "ABERTA",
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Ordem de servico criada.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes da ordem de servico", width="large")
def _view_dialog(scope: str, ordem_id: int) -> None:
    ordem = _find_ordem(ordem_id)
    if ordem is None:
        st.error("Ordem de servico nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, ordem_id)
            st.rerun()
        return

    status = ordem["status"]

    st.text_input("ID", value=str(ordem_id), disabled=True)
    st.text_input(
        "Manutencao",
        value=str(ordem["id_manutencao"]),
        disabled=True,
    )
    st.text_input("Maquina", value=ordem.get("nome_maquina") or "—", disabled=True)
    st.text_input(
        "Status da manutencao",
        value=status_label(ordem.get("status_manutencao"), STATUS_MANUTENCAO_LABELS),
        disabled=True,
    )
    st.text_input(
        "Defeito",
        value=ordem.get("defeito_relatado") or "—",
        disabled=True,
    )
    st.text_area("Descricao", value=ordem.get("descricao") or "", disabled=True)
    st.text_input(
        "Status",
        value=status_label(status, STATUS_ORDEM_LABELS),
        disabled=True,
    )

    st.divider()
    st.caption("Fluxo da ordem de servico")

    if status == "ABERTA":
        if st.button(
            "Iniciar OS",
            use_container_width=True,
            key=f"_iniciar_os_{scope}_{ordem_id}",
        ):
            try:
                api.update_ordem_servico(ordem_id, {"status": "EM_EXECUCAO"})
                toast_ok("Ordem de servico em execucao.")
                clear_dialog_state(scope, ordem_id)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if status == "EM_EXECUCAO":
        if st.button(
            "Concluir OS",
            use_container_width=True,
            key=f"_concluir_os_{scope}_{ordem_id}",
        ):
            try:
                api.concluir_ordem_servico(ordem_id)
                toast_ok("Ordem de servico concluida.")
                clear_dialog_state(scope, ordem_id)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if st.button("Fechar", use_container_width=True, key=f"_fechar_os_{scope}_{ordem_id}"):
        clear_dialog_state(scope, ordem_id)
        st.rerun()


@st.dialog("Editar ordem de servico", width="large")
def _edit_dialog(scope: str, ordem_id: int) -> None:
    ordem = _find_ordem(ordem_id)
    if ordem is None:
        st.error("Ordem de servico nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, ordem_id)
            st.rerun()
        return

    st.caption(
        f"Manutencao #{ordem['id_manutencao']} | "
        f"{ordem.get('nome_maquina') or '—'} | "
        f"Status manutencao: "
        f"{status_label(ordem.get('status_manutencao'), STATUS_MANUTENCAO_LABELS)}"
    )

    descricao = st.text_area(
        "Descricao",
        value=ordem.get("descricao") or "",
        key=f"_edit_os_descricao_{scope}_{ordem_id}",
    )
    ordem_status_options = status_options(STATUS_ORDEM, STATUS_ORDEM_LABELS)
    status_index = (
        STATUS_ORDEM.index(ordem["status"]) if ordem["status"] in STATUS_ORDEM else 0
    )
    status_choice = st.selectbox(
        "Status",
        ordem_status_options,
        index=status_index,
        key=f"_edit_os_status_{scope}_{ordem_id}",
    )

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, ordem_id)
        st.rerun()

    if not salvar:
        return

    try:
        api.update_ordem_servico(
            ordem_id,
            {
                "descricao": descricao.strip() or None,
                "status": status_from_label(
                    status_choice, STATUS_ORDEM, STATUS_ORDEM_LABELS
                ),
            },
        )
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Ordem de servico atualizada.")
    clear_dialog_state(scope, ordem_id)
    st.rerun()


@st.dialog("Excluir ordem de servico")
def _delete_dialog(scope: str, ordem_id: int) -> None:
    ordem = _find_ordem(ordem_id)
    if ordem is None:
        st.error("Ordem de servico nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, ordem_id)
            st.rerun()
        return

    nome = ordem.get("nome_maquina") or "maquina"
    st.warning(
        f"Deseja realmente excluir a OS #{ordem_id} da maquina **{nome}**?\n\n"
        "Essa acao nao podera ser desfeita."
    )

    col1, col2 = st.columns(2)
    with col1:
        excluir = st.button("Excluir", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, ordem_id)
        st.rerun()

    if not excluir:
        return

    try:
        api.delete_ordem_servico(ordem_id)
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Ordem de servico excluida.")
    clear_dialog_state(scope, ordem_id)
    st.rerun()
