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


def _address_state_key(prefix: str) -> str:
    return f"{prefix}_address"


def _default_address_state(defaults=None) -> dict[str, str]:
    return {
        "logradouro": (defaults.logradouro if defaults else "") or "",
        "numero": (defaults.numero if defaults else "") or "",
        "cidade": (defaults.cidade if defaults else "") or "",
        "estado": (defaults.estado if defaults else "") or "",
        "cep": (defaults.cep if defaults else "") or "",
    }


def _apply_pending_cep_lookup(*, prefix: str, state_key: str) -> None:
    """Run ViaCEP lookup on the next rerun, before address widgets are drawn."""
    pending_key = f"{prefix}_pending_cep"
    error_key = f"{prefix}_cep_lookup_error"
    pending_cep = st.session_state.pop(pending_key, None)
    if not pending_cep:
        return

    values = dict(st.session_state[state_key])
    try:
        lookup = client.lookup_address_by_cep(pending_cep)
        if lookup.cep:
            values["cep"] = lookup.cep
        if lookup.logradouro:
            values["logradouro"] = lookup.logradouro
        if lookup.cidade:
            values["cidade"] = lookup.cidade
        if lookup.estado:
            values["estado"] = lookup.estado
        st.session_state[state_key] = values
        if lookup.logradouro:
            st.toast("Endereco encontrado.")
        else:
            st.toast("CEP encontrado. Informe o logradouro manualmente.")
    except LogisticsApiError as exc:
        st.session_state[error_key] = exc.user_message


def _address_form(*, prefix: str, defaults=None) -> dict:
    state_key = _address_state_key(prefix)
    error_key = f"{prefix}_cep_lookup_error"
    if state_key not in st.session_state:
        st.session_state[state_key] = _default_address_state(defaults)

    _apply_pending_cep_lookup(prefix=prefix, state_key=state_key)

    lookup_error = st.session_state.pop(error_key, None)
    if lookup_error:
        st.error(lookup_error)

    values = st.session_state[state_key]

    st.subheader("Endereco")
    cep_col, btn_col = st.columns([3, 1])
    with cep_col:
        cep_value = st.text_input("CEP", value=values["cep"])
    with btn_col:
        st.write("")
        st.write("")
        buscar = st.button(
            "Buscar CEP",
            key=f"{prefix}_buscar_cep",
            use_container_width=True,
        )

    if buscar:
        if not cep_value.strip():
            st.error("Informe o CEP.")
        else:
            st.session_state[f"{prefix}_pending_cep"] = cep_value.strip()
            st.rerun()

    values["cep"] = cep_value
    values["logradouro"] = st.text_input("Logradouro", value=values["logradouro"])
    values["numero"] = st.text_input("Numero", value=values["numero"])
    values["cidade"] = st.text_input("Cidade", value=values["cidade"])
    values["estado"] = st.text_input(
        "Estado (UF)",
        value=values["estado"],
        max_chars=2,
    )
    st.session_state[state_key] = values
    return dict(values)


def _parse_address(raw: dict) -> AddressCreateSchema | None:
    logradouro = raw["logradouro"].strip()
    cidade = raw["cidade"].strip()
    estado = raw["estado"].strip()
    if not logradouro and not cidade and not estado:
        return None
    if not logradouro or not cidade or not estado:
        raise ValueError("Informe logradouro, cidade e estado.")
    return AddressCreateSchema(
        logradouro=logradouro,
        numero=raw["numero"].strip() or None,
        cidade=cidade,
        estado=estado,
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
    endereco = loc.endereco
    st.subheader("Endereco")
    st.text_input(
        "ID endereco",
        value=str(endereco.id_endereco) if endereco else "",
        disabled=True,
    )
    st.text_input(
        "Logradouro",
        value=endereco.logradouro if endereco else "",
        disabled=True,
    )
    st.text_input(
        "Numero",
        value=endereco.numero or "" if endereco else "",
        disabled=True,
    )
    st.text_input(
        "Cidade",
        value=endereco.cidade if endereco else "",
        disabled=True,
    )
    st.text_input(
        "Estado",
        value=endereco.estado if endereco else "",
        disabled=True,
    )
    st.text_input(
        "CEP",
        value=endereco.cep or "" if endereco else "",
        disabled=True,
    )
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
