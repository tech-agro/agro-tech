"""Diálogos da entidade Cliente."""

from __future__ import annotations

import streamlit as st

from app.comercial.enum import StatusCliente
from app.comercial.models import NovoCliente
from components.comercial.dialog_state import clear_dialog_state, get_dialog
from components.comercial.formatters import STATUS_CLIENTE_LABELS
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
        elif kind == "edit":
            _edit_dialog(scope, entity_id)
        elif kind == "delete":
            _delete_dialog(scope, entity_id)


@st.dialog("Novo cliente", width="large")
def _create_dialog(scope: str) -> None:
    state_key = f"_novo_cliente_cnpj_data_{scope}"

    documento = st.text_input("Documento (CPF/CNPJ)", key=f"_novo_cliente_documento_{scope}")

    col_buscar, _ = st.columns([1, 3])
    with col_buscar:
        buscar_cnpj = st.button("Buscar CNPJ", use_container_width=True)

    if buscar_cnpj:
        documento_limpo = "".join(ch for ch in documento if ch.isdigit())
        if len(documento_limpo) != 14:
            st.error("Informe um CNPJ valido (14 digitos) para buscar.")
        else:
            try:
                empresa = client.lookup_empresa_por_cnpj(documento_limpo)
                st.session_state[state_key] = empresa
                st.toast("Dados da empresa encontrados.")
            except ComercialApiError as exc:
                st.session_state.pop(state_key, None)
                st.error(exc.user_message)

    empresa = st.session_state.get(state_key)

    nome_sugerido = empresa.razao_social if empresa else ""
    nome = st.text_input("Nome", value=nome_sugerido)

    if empresa:
        st.caption(
            f"**{empresa.nome_fantasia or empresa.razao_social}** — "
            f"{empresa.situacao_cadastral or 'situacao desconhecida'}"
        )
        if empresa.logradouro:
            endereco = f"{empresa.logradouro}, {empresa.numero or 's/n'} — {empresa.bairro or ''}"
            endereco += f" — {empresa.municipio or ''}/{empresa.uf or ''}"
            st.caption(endereco)

    status = st.selectbox(
        "Status",
        options=list(StatusCliente),
        format_func=lambda s: STATUS_CLIENTE_LABELS.get(s, s.value) or "",
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

    if not nome.strip() or not documento.strip():
        st.error("Informe nome e documento do cliente.")
        return

    try:
        client.create_cliente(NovoCliente(nome=nome.strip(), documento=documento.strip(), status=status))
    except ComercialApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Cliente criado com sucesso.")
    st.session_state.pop(state_key, None)
    clear_dialog_state(scope)
    st.rerun()


def _find_cliente(id_cliente: int):
    for cliente in client.list_clientes():
        if cliente.id_cliente == id_cliente:
            return cliente
    return None


@st.dialog("Detalhes do cliente", width="large")
def _view_dialog(scope: str, id_cliente: int) -> None:
    cliente = _find_cliente(id_cliente)
    if cliente is None:
        st.error("Cliente não encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, id_cliente)
            st.rerun()
        return

    st.text_input("Cliente", cliente.pessoa_nome or f"#{cliente.id_pessoa}", disabled=True)
    st.text_input("Status", STATUS_CLIENTE_LABELS.get(cliente.status, cliente.status.value), disabled=True)

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, id_cliente)
        st.rerun()


@st.dialog("Editar status do cliente", width="large")
def _edit_dialog(scope: str, id_cliente: int) -> None:
    cliente = _find_cliente(id_cliente)
    if cliente is None:
        st.error("Cliente não encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, id_cliente)
            st.rerun()
        return

    novo_status = st.selectbox(
        "Status",
        options=list(StatusCliente),
        index=list(StatusCliente).index(cliente.status),
        format_func=lambda s: STATUS_CLIENTE_LABELS.get(s, s.value) or "",
    )

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, id_cliente)
        st.rerun()

    if not salvar:
        return

    try:
        client.update_status_cliente(id_cliente, novo_status)
    except ComercialApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Cliente atualizado com sucesso.")
    clear_dialog_state(scope, id_cliente)
    st.rerun()


@st.dialog("Excluir cliente")
def _delete_dialog(scope: str, id_cliente: int) -> None:
    cliente = _find_cliente(id_cliente)
    if cliente is None:
        st.error("Cliente não encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, id_cliente)
            st.rerun()
        return

    st.warning(
        f"Deseja realmente excluir o cliente **{cliente.pessoa_nome or f'#{cliente.id_pessoa}'}**?\n\n"
        "Essa ação não poderá ser desfeita."
    )

    col1, col2 = st.columns(2)
    with col1:
        excluir = st.button("Excluir", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, id_cliente)
        st.rerun()

    if not excluir:
        return

    try:
        client.delete_cliente(id_cliente)
    except ComercialApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope, id_cliente)
            st.rerun()
        return

    st.toast("Cliente excluído com sucesso.")
    clear_dialog_state(scope, id_cliente)
    st.rerun()
