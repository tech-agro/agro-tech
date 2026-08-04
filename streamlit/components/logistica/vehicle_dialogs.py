"""Dialogos da entidade veiculo."""

from __future__ import annotations

import streamlit as st

from app.logistica.enum import VehicleType
from app.logistica.schemas.vehicle import VehicleCreateSchema, VehicleUpdateSchema
from components.logistica.dialog_state import clear_dialog_state, get_dialog
from components.logistica.formatters import VEHICLE_TYPE_LABELS, vehicle_type_label
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


@st.dialog("Novo veiculo")
def _create(scope: str) -> None:
    tipos = list(VehicleType)
    tipo = st.selectbox(
        "Tipo",
        tipos,
        format_func=lambda t: VEHICLE_TYPE_LABELS[t],
    )
    placa = st.text_input("Placa")
    capacidade = st.number_input("Capacidade", min_value=0.0, step=0.01, value=0.0)
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
        if not placa.strip():
            raise ValueError("Informe a placa.")
        client.create_vehicle(
            VehicleCreateSchema(
                tipo=tipo,
                placa=placa.strip().upper(),
                capacidade=capacidade if capacidade > 0 else None,
            )
        )
        st.toast("Veiculo cadastrado.")
        clear_dialog_state(scope)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
    except LogisticsApiError as exc:
        st.error(exc.user_message)


@st.dialog("Detalhes do veiculo")
def _view(scope: str, vehicle_id: int) -> None:
    try:
        vehicle = client.get_vehicle(vehicle_id)
    except LogisticsApiError as exc:
        st.error(exc.user_message)
        return
    st.text_input("ID veiculo", value=str(vehicle.id_veiculo), disabled=True)
    st.text_input("Tipo", value=vehicle_type_label(vehicle.tipo), disabled=True)
    st.text_input("Placa", value=vehicle.placa, disabled=True)
    st.text_input(
        "Capacidade",
        value="" if vehicle.capacidade is None else str(vehicle.capacidade),
        disabled=True,
    )
    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, vehicle_id)
        st.rerun()


@st.dialog("Editar veiculo")
def _edit(scope: str, vehicle_id: int) -> None:
    try:
        vehicle = client.get_vehicle(vehicle_id)
    except LogisticsApiError as exc:
        st.error(exc.user_message)
        return
    tipos = list(VehicleType)
    tipo_idx = tipos.index(vehicle.tipo) if vehicle.tipo in tipos else 0
    tipo = st.selectbox(
        "Tipo",
        tipos,
        index=tipo_idx,
        format_func=lambda t: VEHICLE_TYPE_LABELS[t],
    )
    placa = st.text_input("Placa", value=vehicle.placa)
    capacidade = st.number_input(
        "Capacidade",
        min_value=0.0,
        step=0.01,
        value=float(vehicle.capacidade or 0),
    )
    c1, c2 = st.columns(2)
    with c1:
        save = st.button("Salvar", type="primary", use_container_width=True)
    with c2:
        cancel = st.button("Cancelar", use_container_width=True)
    if cancel:
        clear_dialog_state(scope, vehicle_id)
        st.rerun()
    if not save:
        return
    try:
        if not placa.strip():
            raise ValueError("Informe a placa.")
        client.update_vehicle(
            vehicle_id,
            VehicleUpdateSchema(
                tipo=tipo,
                placa=placa.strip().upper(),
                capacidade=capacidade if capacidade > 0 else None,
            ),
        )
        st.toast("Veiculo atualizado.")
        clear_dialog_state(scope, vehicle_id)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
    except LogisticsApiError as exc:
        st.error(exc.user_message)


@st.dialog("Excluir veiculo")
def _delete(scope: str, vehicle_id: int) -> None:
    st.write(f"Confirma excluir o veiculo #{vehicle_id}?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Excluir", type="primary", use_container_width=True):
            try:
                client.delete_vehicle(vehicle_id)
                st.toast("Veiculo excluido.")
                clear_dialog_state(scope, vehicle_id)
                st.rerun()
            except LogisticsApiError as exc:
                st.error(exc.user_message)
    with c2:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state(scope, vehicle_id)
            st.rerun()
