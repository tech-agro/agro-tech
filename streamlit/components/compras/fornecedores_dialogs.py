"""Dialogs for the Supplier entity."""

from __future__ import annotations

import streamlit as st

from app.compras.schemas.supplier import SupplierCreateSchema, SupplierUpdateSchema
from components.compras.dialog_state import clear_dialog_state, get_dialog
from services.compras_client import PurchasesApiError, PurchasesClient

client = PurchasesClient()


def render(scope: str = "fornecedores") -> None:
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


@st.dialog("Novo fornecedor", width="large")
def _create_dialog(scope: str) -> None:
    """Mirrors Comercial cliente create + BrasilAPI CNPJ autocomplete."""
    state_key = f"_novo_fornecedor_cnpj_data_{scope}"

    documento = st.text_input(
        "Documento (CNPJ/CPF)", key=f"_novo_fornecedor_documento_{scope}"
    )

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
            except PurchasesApiError as exc:
                st.session_state.pop(state_key, None)
                st.error(exc.user_message)

    empresa = st.session_state.get(state_key)
    nome_sugerido = empresa.razao_social if empresa else ""
    nome = st.text_input("Nome / razao social", value=nome_sugerido)

    if empresa:
        st.caption(
            f"**{empresa.nome_fantasia or empresa.razao_social}** — "
            f"{empresa.situacao_cadastral or 'situacao desconhecida'}"
        )
        if empresa.logradouro:
            endereco = (
                f"{empresa.logradouro}, {empresa.numero or 's/n'} — "
                f"{empresa.bairro or ''}"
            )
            endereco += f" — {empresa.municipio or ''}/{empresa.uf or ''}"
            st.caption(endereco)

    categoria = st.text_input("Categoria")

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
        st.error("Informe nome e documento do fornecedor.")
        return

    try:
        client.create_supplier(
            SupplierCreateSchema(
                nome=nome.strip(),
                documento=documento.strip(),
                categoria=categoria.strip() or None,
            )
        )
    except PurchasesApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Fornecedor criado com sucesso.")
    st.session_state.pop(state_key, None)
    clear_dialog_state(scope)
    st.rerun()


def _find_supplier(supplier_id: int):
    try:
        return client.get_supplier(supplier_id)
    except PurchasesApiError:
        return None


@st.dialog("Detalhes do fornecedor", width="large")
def _view_dialog(scope: str, supplier_id: int) -> None:
    supplier = _find_supplier(supplier_id)
    if supplier is None:
        st.error("Fornecedor nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, supplier_id)
            st.rerun()
        return

    st.text_input("Nome", supplier.nome, disabled=True)
    st.text_input("Documento", supplier.documento, disabled=True)
    st.text_input("Categoria", supplier.categoria or "—", disabled=True)

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, supplier_id)
        st.rerun()


@st.dialog("Editar fornecedor", width="large")
def _edit_dialog(scope: str, supplier_id: int) -> None:
    supplier = _find_supplier(supplier_id)
    if supplier is None:
        st.error("Fornecedor nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, supplier_id)
            st.rerun()
        return

    nome = st.text_input("Nome / razao social", value=supplier.nome)
    documento = st.text_input("Documento (CNPJ/CPF)", value=supplier.documento)
    categoria = st.text_input("Categoria", value=supplier.categoria or "")

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, supplier_id)
        st.rerun()

    if not salvar:
        return

    if not nome.strip() or not documento.strip():
        st.error("Informe nome e documento do fornecedor.")
        return

    try:
        client.update_supplier(
            supplier_id,
            SupplierUpdateSchema(
                nome=nome.strip(),
                documento=documento.strip(),
                categoria=categoria.strip() or None,
            ),
        )
    except PurchasesApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Fornecedor atualizado com sucesso.")
    clear_dialog_state(scope, supplier_id)
    st.rerun()


@st.dialog("Excluir fornecedor")
def _delete_dialog(scope: str, supplier_id: int) -> None:
    supplier = _find_supplier(supplier_id)
    if supplier is None:
        st.error("Fornecedor nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, supplier_id)
            st.rerun()
        return

    st.warning(
        f"Deseja realmente excluir o fornecedor **{supplier.nome}**?\n\n"
        "Essa acao nao podera ser desfeita."
    )

    col1, col2 = st.columns(2)
    with col1:
        excluir = st.button("Excluir", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, supplier_id)
        st.rerun()

    if not excluir:
        return

    try:
        client.delete_supplier(supplier_id)
    except PurchasesApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope, supplier_id)
            st.rerun()
        return

    st.toast("Fornecedor excluido com sucesso.")
    clear_dialog_state(scope, supplier_id)
    st.rerun()
