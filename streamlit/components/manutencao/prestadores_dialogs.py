"""Dialogs for service providers (prestadores)."""

from __future__ import annotations

import streamlit as st

from components.manutencao.dialog_state import clear_dialog_state, get_dialog
from components.shared.screens import toast_ok
import services.manutencao_client as api

SCOPE = "prestadores"


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


def _find_prestador(prestador_id: int) -> dict | None:
    try:
        return api.get_prestador(prestador_id)
    except Exception:
        return None


@st.dialog("Novo prestador", width="large")
def _create_dialog(scope: str) -> None:
    state_key = f"_novo_prestador_cnpj_data_{scope}"

    cnpj = st.text_input("CNPJ", key=f"_novo_prestador_cnpj_{scope}")

    col_buscar, _ = st.columns([1, 3])
    with col_buscar:
        buscar_cnpj = st.button("Buscar CNPJ", use_container_width=True)

    if buscar_cnpj:
        digits = "".join(ch for ch in cnpj if ch.isdigit())
        if len(digits) != 14:
            st.error("Informe um CNPJ valido (14 digitos).")
        else:
            try:
                empresa = api.lookup_empresa_por_cnpj(digits)
                st.session_state[state_key] = empresa
                st.toast("Dados da empresa encontrados.")
            except Exception as exc:
                st.session_state.pop(state_key, None)
                st.error(str(exc))

    empresa = st.session_state.get(state_key) or {}
    nome_sugerido = empresa.get("razao_social") or ""

    if empresa:
        st.caption(
            f"**{empresa.get('nome_fantasia') or empresa.get('razao_social')}** — "
            f"{empresa.get('situacao_cadastral') or 'situacao desconhecida'}"
        )
        if empresa.get("logradouro"):
            endereco = (
                f"{empresa.get('logradouro')}, {empresa.get('numero') or 's/n'} — "
                f"{empresa.get('bairro') or ''}"
            )
            endereco += f" — {empresa.get('municipio') or ''}/{empresa.get('uf') or ''}"
            st.caption(endereco)

    nome = st.text_input("Nome / razao social", value=nome_sugerido)
    especialidade = st.text_input(
        "Especialidade",
        placeholder="Mecanica, eletrica...",
        key=f"_novo_prestador_especialidade_{scope}",
    )
    telefone = st.text_input(
        "Telefone",
        placeholder="81999999999",
        key=f"_novo_prestador_telefone_{scope}",
    )

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        st.session_state.pop(state_key, None)
        clear_dialog_state(scope)
        st.rerun()

    if not salvar:
        return

    if not nome.strip() or not cnpj.strip():
        st.error("Informe nome e CNPJ.")
        return
    if not especialidade.strip() or not telefone.strip():
        st.error("Informe especialidade e telefone.")
        return

    try:
        api.create_prestador(
            {
                "nome": nome.strip(),
                "cnpj": cnpj.strip(),
                "especialidade": especialidade.strip(),
                "telefone": telefone.strip(),
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Prestador cadastrado.")
    st.session_state.pop(state_key, None)
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes do prestador", width="large")
def _view_dialog(scope: str, prestador_id: int) -> None:
    prestador = _find_prestador(prestador_id)
    if prestador is None:
        st.error("Prestador nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, prestador_id)
            st.rerun()
        return

    st.text_input("ID", value=str(prestador["id_prestador"]), disabled=True)
    st.text_input("Nome", value=prestador["nome"], disabled=True)
    st.text_input("CNPJ", value=prestador["cnpj"], disabled=True)
    st.text_input("Especialidade", value=prestador["especialidade"], disabled=True)
    st.text_input("Telefone", value=prestador["telefone"], disabled=True)

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, prestador_id)
        st.rerun()


@st.dialog("Editar prestador", width="large")
def _edit_dialog(scope: str, prestador_id: int) -> None:
    prestador = _find_prestador(prestador_id)
    if prestador is None:
        st.error("Prestador nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, prestador_id)
            st.rerun()
        return

    nome = st.text_input(
        "Nome / razao social",
        value=prestador["nome"],
        key=f"_edit_prestador_nome_{scope}_{prestador_id}",
    )
    cnpj = st.text_input(
        "CNPJ",
        value=prestador["cnpj"],
        key=f"_edit_prestador_cnpj_{scope}_{prestador_id}",
    )
    especialidade = st.text_input(
        "Especialidade",
        value=prestador["especialidade"],
        key=f"_edit_prestador_especialidade_{scope}_{prestador_id}",
    )
    telefone = st.text_input(
        "Telefone",
        value=prestador["telefone"],
        key=f"_edit_prestador_telefone_{scope}_{prestador_id}",
    )

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, prestador_id)
        st.rerun()

    if not salvar:
        return

    if not nome.strip() or not cnpj.strip():
        st.error("Informe nome e CNPJ.")
        return
    if not especialidade.strip() or not telefone.strip():
        st.error("Informe especialidade e telefone.")
        return

    try:
        api.update_prestador(
            prestador_id,
            {
                "nome": nome.strip(),
                "cnpj": cnpj.strip(),
                "especialidade": especialidade.strip(),
                "telefone": telefone.strip(),
            },
        )
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Prestador atualizado.")
    clear_dialog_state(scope, prestador_id)
    st.rerun()


@st.dialog("Excluir prestador")
def _delete_dialog(scope: str, prestador_id: int) -> None:
    prestador = _find_prestador(prestador_id)
    if prestador is None:
        st.error("Prestador nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, prestador_id)
            st.rerun()
        return

    st.warning(
        f"Deseja realmente excluir o prestador **{prestador['nome']}**?\n\n"
        "Essa acao nao podera ser desfeita."
    )

    col1, col2 = st.columns(2)
    with col1:
        excluir = st.button("Excluir", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, prestador_id)
        st.rerun()

    if not excluir:
        return

    try:
        api.delete_prestador(prestador_id)
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Prestador excluido.")
    clear_dialog_state(scope, prestador_id)
    st.rerun()
