"""Dialogos da entidade local_logistico (+ endereco opcional)."""

from __future__ import annotations

import streamlit as st

from app.logistica.enum import LocationType
from app.logistica.schemas.address import AddressCreateSchema
from app.logistica.schemas.location import LocationCreateSchema, LocationUpdateSchema
from components.logistica.dialog_state import clear_dialog_state, get_dialog
from components.logistica.formatters import LOCATION_TYPE_LABELS, location_type_label
from services.logistica_client import LogisticsApiError, LogisticsClient

client = LogisticsClient()


def render(scope: str) -> None:
    dialog = get_dialog(scope)
    if dialog is None:
        return
    kind, entity_id = dialog
    if kind == "create":
        _create(scope)
    elif entity_id is not None and kind == "view":
        _view(scope, entity_id)
    elif entity_id is not None and kind == "edit":
        _edit(scope, entity_id)
    elif entity_id is not None and kind == "delete":
        _delete(scope, entity_id)


def _address_form(*, prefix: str, defaults=None) -> dict | None:
    with_address = st.checkbox(
        "Informar endereco",
        value=defaults is not None,
        key=f"{prefix}_with_address",
    )
    if not with_address:
        return None
    logradouro = st.text_input(
        "Logradouro",
        value=defaults.logradouro if defaults else "",
        key=f"{prefix}_logradouro",
    )
    numero = st.text_input(
        "Numero",
        value=(defaults.numero or "") if defaults else "",
        key=f"{prefix}_numero",
    )
    cidade = st.text_input(
        "Cidade",
        value=defaults.cidade if defaults else "",
        key=f"{prefix}_cidade",
    )
    estado = st.text_input(
        "Estado (UF)",
        value=defaults.estado if defaults else "",
        max_chars=2,
        key=f"{prefix}_estado",
    )
    cep = st.text_input(
        "CEP",
        value=(defaults.cep or "") if defaults else "",
        key=f"{prefix}_cep",
    )
    return {
        "logradouro": logradouro,
        "numero": numero,
        "cidade": cidade,
        "estado": estado,
        "cep": cep,
    }


def _parse_address(raw: dict | None) -> AddressCreateSchema | None:
    if raw is None:
        return None
    if not raw["logradouro"].strip() or not raw["cidade"].strip() or not raw["estado"].strip():
        raise ValueError("Informe logradouro, cidade e estado.")
    return AddressCreateSchema(
        logradouro=raw["logradouro"].strip(),
        numero=raw["numero"].strip() or None,
        cidade=raw["cidade"].strip(),
        estado=raw["estado"].strip(),
        cep=raw["cep"].strip() or None,
    )


@st.dialog("Novo local", width="large")
def _create(scope: str) -> None:
    nome = st.text_input("Nome")
    tipos = list(LocationType)
    tipo = st.selectbox(
        "Tipo",
        tipos,
        format_func=lambda t: LOCATION_TYPE_LABELS[t],
    )
    address_raw = _address_form(prefix="loc_create")
    c1, c2 = st.columns(2)
    with c1:
        save = st.button("Salvar", type="primary", use_container_width=True)
    with c2:
        cancel = st.button("Cancelar", use_container_width=True)
    if cancel:
        clear_dialog_state(scope)
        st.rerun()
    if not save:
        return
    try:
        if not nome.strip():
            raise ValueError("Informe o nome.")
        client.create_location(
            LocationCreateSchema(
                nome=nome.strip(),
                tipo=tipo,
                endereco=_parse_address(address_raw),
            )
        )
        st.toast("Local cadastrado.")
        clear_dialog_state(scope)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
    except LogisticsApiError as exc:
        st.error(exc.user_message)


@st.dialog("Detalhes do local", width="large")
def _view(scope: str, location_id: int) -> None:
    try:
        loc = client.get_location(location_id)
    except LogisticsApiError as exc:
        st.error(exc.user_message)
        return
    st.text_input("ID local", value=str(loc.id_local_logistico), disabled=True)
    st.text_input("Nome", value=loc.nome, disabled=True)
    st.text_input("Tipo", value=location_type_label(loc.tipo), disabled=True)
    if loc.endereco:
        st.text_input("ID endereco", value=str(loc.endereco.id_endereco), disabled=True)
        st.text_input("Logradouro", value=loc.endereco.logradouro, disabled=True)
        st.text_input("Numero", value=loc.endereco.numero or "", disabled=True)
        st.text_input("Cidade", value=loc.endereco.cidade, disabled=True)
        st.text_input("Estado", value=loc.endereco.estado, disabled=True)
        st.text_input("CEP", value=loc.endereco.cep or "", disabled=True)
    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, location_id)
        st.rerun()


@st.dialog("Editar local", width="large")
def _edit(scope: str, location_id: int) -> None:
    try:
        loc = client.get_location(location_id)
    except LogisticsApiError as exc:
        st.error(exc.user_message)
        return
    nome = st.text_input("Nome", value=loc.nome)
    tipos = list(LocationType)
    tipo_idx = tipos.index(loc.tipo) if loc.tipo in tipos else 0
    tipo = st.selectbox(
        "Tipo",
        tipos,
        index=tipo_idx,
        format_func=lambda t: LOCATION_TYPE_LABELS[t],
    )
    address_raw = _address_form(prefix=f"loc_edit_{location_id}", defaults=loc.endereco)
    c1, c2 = st.columns(2)
    with c1:
        save = st.button("Salvar", type="primary", use_container_width=True)
    with c2:
        cancel = st.button("Cancelar", use_container_width=True)
    if cancel:
        clear_dialog_state(scope, location_id)
        st.rerun()
    if not save:
        return
    try:
        if not nome.strip():
            raise ValueError("Informe o nome.")
        payload = LocationUpdateSchema(nome=nome.strip(), tipo=tipo)
        if address_raw is not None:
            payload = LocationUpdateSchema(
                nome=nome.strip(),
                tipo=tipo,
                endereco=_parse_address(address_raw),
            )
        client.update_location(location_id, payload)
        st.toast("Local atualizado.")
        clear_dialog_state(scope, location_id)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
    except LogisticsApiError as exc:
        st.error(exc.user_message)


@st.dialog("Excluir local")
def _delete(scope: str, location_id: int) -> None:
    st.write(f"Confirma excluir o local #{location_id}?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Excluir", type="primary", use_container_width=True):
            try:
                client.delete_location(location_id)
                st.toast("Local excluido.")
                clear_dialog_state(scope, location_id)
                st.rerun()
            except LogisticsApiError as exc:
                st.error(exc.user_message)
    with c2:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state(scope, location_id)
            st.rerun()
