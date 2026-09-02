"""Dialogos da entidade operacao_logistica.

Fluxo operacional em abas:
Operacao → Cargas → Pesagens → Expedicao
"""

from __future__ import annotations

from datetime import date, datetime, time

import streamlit as st

from app.logistica.enum import DispatchStatus, OperationStatus, OperationType
from app.logistica.schemas.dispatch import DispatchCreateSchema, DispatchUpdateSchema
from app.logistica.schemas.operation import (
    OperationCreateSchema,
    OperationUpdateSchema,
)
from app.logistica.schemas.weighing import WeighingCreateSchema
from components.logistica.dialog_state import clear_dialog_state, get_dialog
from components.logistica.formatters import (
    DISPATCH_STATUS_LABELS,
    OPERATION_STATUS_LABELS,
    OPERATION_TYPE_LABELS,
    driver_label,
    location_label,
    lot_label,
    sale_label,
    vehicle_label,
    vehicle_type_label,
)
from components.logistica.loads_editor import (
    collect_load_creates,
    loads_data_editor,
    persist_load_rows,
)
from components.logistica.operation_tables import (
    loads_view_column_config,
    loads_view_df,
    weighings_view_column_config,
    weighings_view_df,
)
from services.logistica_client import LogisticsApiError, LogisticsClient

client = LogisticsClient()
SCOPE = "operacoes"


def render(scope: str = SCOPE) -> None:
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


def _sale_captions(sales_by_id: dict, sale_id: int) -> None:
    sale = sales_by_id.get(sale_id)
    if sale is None:
        return
    if sale.cliente_nome:
        st.caption(f"Cliente: {sale.cliente_nome}")
    if sale.data_venda:
        st.caption(f"Data venda: {sale.data_venda.isoformat()}")


def _as_date(value: datetime | None) -> date | None:
    if value is None:
        return None
    return value.date() if isinstance(value, datetime) else value


def _optional_datetime(
    *,
    label: str,
    key: str,
    current: datetime | None,
    enabled_label: str,
) -> datetime | None:
    enabled = st.checkbox(
        enabled_label,
        value=current is not None,
        key=f"{key}_enabled",
    )
    if not enabled:
        return None
    chosen = st.date_input(
        label,
        value=_as_date(current) or date.today(),
        key=f"{key}_date",
    )
    return datetime.combine(chosen, time.min)


def _driver_select(
    *,
    key: str,
    current_id: int | None,
    drivers: list,
) -> int | None:
    if not drivers:
        st.info("Nenhum motorista cadastrado (padrao: Motorista 1, Motorista 2).")
        return None
    drivers_by_id = {d.id_funcionario: d for d in drivers}
    options: list[int | None] = [None, *[d.id_funcionario for d in drivers]]
    default_idx = 0
    if current_id in drivers_by_id:
        default_idx = options.index(current_id)
    selected = st.selectbox(
        "ID motorista",
        options,
        index=default_idx,
        format_func=lambda i: "—" if i is None else drivers_by_id[i].nome,
        key=key,
    )
    if selected is not None:
        st.caption(f"Motorista: {driver_label(drivers_by_id[selected])}")
    return selected


@st.dialog("Nova operacao", width="large")
def _create(scope: str) -> None:
    try:
        vehicles = client.list_vehicles_options()
        locations = client.list_locations_options()
        sales = client.list_sales()
        lots = client.list_lots()
    except LogisticsApiError as exc:
        st.error(exc.user_message)
        return

    if not vehicles or not locations:
        st.warning("Cadastre veiculo e locais antes de criar operacoes.")
        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()
        return

    vehicles_by_id = {v.id_veiculo: v for v in vehicles}
    locations_by_id = {loc.id_local_logistico: loc for loc in locations}
    sales_by_id = {s.id_venda: s for s in sales}
    location_ids = list(locations_by_id.keys())
    lot_map = {lot_label(lot): lot.id_lote for lot in lots}

    tab_op, tab_cargas = st.tabs(["Operacao", "Cargas"])

    with tab_op:
        id_veiculo = st.selectbox(
            "Veiculo",
            [v.id_veiculo for v in vehicles],
            format_func=lambda i: vehicles_by_id[i].placa,
        )
        st.caption(f"Tipo: {vehicle_type_label(vehicles_by_id[id_veiculo].tipo)}")

        id_origem = st.selectbox(
            "Origem",
            location_ids,
            format_func=lambda i: locations_by_id[i].nome,
        )
        id_destino = st.selectbox(
            "Destino",
            location_ids,
            index=1 if len(location_ids) > 1 else 0,
            format_func=lambda i: locations_by_id[i].nome,
        )

        type_values = list(OperationType)
        type_labels = [OPERATION_TYPE_LABELS[t] for t in type_values]
        type_label = st.selectbox("Tipo", type_labels, index=0)
        op_type = type_values[type_labels.index(type_label)]

        id_venda = None
        suggest_from_sale = False
        if op_type == OperationType.VENDA:
            if not sales:
                st.warning("Cadastre/confirme uma venda no modulo Comercial.")
                if st.button("Fechar"):
                    clear_dialog_state(scope)
                    st.rerun()
                return
            id_venda = st.selectbox(
                "Venda",
                [s.id_venda for s in sales],
                format_func=lambda i: sale_label(sales_by_id[i]),
            )
            _sale_captions(sales_by_id, id_venda)
            suggest_from_sale = st.checkbox(
                "Sugerir cargas a partir do picking da venda",
                value=True,
            )

        status_values = list(OperationStatus)
        status_labels = [OPERATION_STATUS_LABELS[s] for s in status_values]
        status_label = st.selectbox("Status", status_labels, index=0)

    with tab_cargas:
        if suggest_from_sale:
            st.info(
                "As cargas serao montadas a partir do picking da venda confirmada "
                "(Comercial). Deixe a grade vazia."
            )
        else:
            st.caption(
                "Informe lotes com saldo disponivel no Estoque. "
                "Ao criar, a expedicao inicia Em preparacao."
            )
        loads_df = None
        if lots and not suggest_from_sale:
            loads_df = loads_data_editor(
                state_key="new_operation_loads",
                editor_key="new_operation_loads_editor",
                lots=lots,
                with_ids=False,
            )
        elif not lots and not suggest_from_sale:
            st.info("Nenhum lote com saldo disponivel no Estoque para carregar.")

    c1, c2 = st.columns(2)
    with c1:
        save = st.button("Criar", type="primary", use_container_width=True)
    with c2:
        cancel = st.button("Cancelar", use_container_width=True)
    if cancel:
        clear_dialog_state(scope)
        st.rerun()
    if not save:
        return
    try:
        if id_origem == id_destino:
            raise ValueError("Origem e destino devem ser diferentes.")
        cargas = (
            []
            if suggest_from_sale
            else (collect_load_creates(loads_df, lot_map) if loads_df is not None else [])
        )
        client.create_operation(
            OperationCreateSchema(
                id_veiculo=id_veiculo,
                id_origem=id_origem,
                id_destino=id_destino,
                id_venda=id_venda,
                tipo=op_type,
                data_inicio=datetime.now(),
                status=status_values[status_labels.index(status_label)],
                cargas=cargas,
                suggest_loads_from_sale=suggest_from_sale,
            )
        )
        st.toast("Operacao criada.")
        clear_dialog_state(scope)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
    except LogisticsApiError as exc:
        st.error(exc.user_message)


@st.dialog("Detalhes da operacao", width="large")
def _view(scope: str, operation_id: int) -> None:
    try:
        operation = client.get_operation(operation_id)
        loads = client.list_loads(operation_id)
    except LogisticsApiError as exc:
        st.error(exc.user_message)
        return

    tab_op, tab_cargas, tab_pesagens, tab_exp = st.tabs(
        ["Operacao", "Cargas", "Pesagens", "Expedicao"]
    )

    with tab_op:
        a1, a2 = st.columns(2)
        with a1:
            st.text_input("ID operacao", value=str(operation.id_operacao), disabled=True)
            st.text_input("ID veiculo", value=str(operation.id_veiculo), disabled=True)
            st.text_input("Placa", value=operation.veiculo_placa or "", disabled=True)
            st.text_input("ID origem", value=str(operation.id_origem), disabled=True)
            st.text_input("Origem", value=operation.origem_nome or "", disabled=True)
        with a2:
            st.text_input("ID destino", value=str(operation.id_destino), disabled=True)
            st.text_input("Destino", value=operation.destino_nome or "", disabled=True)
            st.text_input(
                "Venda",
                value=(
                    str(operation.id_venda) if operation.id_venda is not None else "—"
                ),
                disabled=True,
            )
            st.text_input("Cliente", value=operation.cliente_nome or "", disabled=True)
            st.text_input(
                "Status",
                value=OPERATION_STATUS_LABELS.get(
                    operation.status, operation.status.value
                ),
                disabled=True,
            )

    with tab_cargas:
        st.dataframe(loads_view_df(loads), hide_index=True, column_config=loads_view_column_config())

    with tab_pesagens:
        if not loads:
            st.info("Nenhuma carga vinculada.")
        else:
            load_ids = [load.id_carga for load in loads]
            loads_by_id = {load.id_carga: load for load in loads}
            id_carga = st.selectbox(
                "ID carga", load_ids, format_func=str, key=f"view_pesagem_{operation_id}"
            )
            load = loads_by_id[id_carga]
            st.caption(f"Codigo lote: {load.lote_codigo or ''}")
            try:
                weighings = client.list_weighings(operation_id, id_carga)
            except LogisticsApiError as exc:
                st.error(exc.user_message)
                return
            st.dataframe(
                weighings_view_df(weighings),
                hide_index=True,
                column_config=weighings_view_column_config(),
            )

    with tab_exp:
        if not loads:
            st.info("Nenhuma carga vinculada.")
        else:
            load_ids = [load.id_carga for load in loads]
            id_carga = st.selectbox(
                "ID carga", load_ids, format_func=str, key=f"view_exp_{operation_id}"
            )
            try:
                dispatch = client.get_dispatch(operation_id, id_carga)
            except LogisticsApiError as exc:
                st.error(exc.user_message)
                return
            if dispatch is None:
                st.info("Expedicao ainda nao iniciada para esta carga.")
            else:
                st.text_input(
                    "Status",
                    value=DISPATCH_STATUS_LABELS.get(
                        dispatch.status, dispatch.status.value
                    ),
                    disabled=True,
                )
                st.text_input(
                    "Data saida",
                    value=(
                        dispatch.data_saida.isoformat(sep=" ", timespec="minutes")
                        if dispatch.data_saida
                        else ""
                    ),
                    disabled=True,
                )
                st.text_input(
                    "Data chegada prevista",
                    value=(
                        dispatch.data_chegada_prevista.isoformat(
                            sep=" ", timespec="minutes"
                        )
                        if dispatch.data_chegada_prevista
                        else ""
                    ),
                    disabled=True,
                )
                st.text_input(
                    "Data entrega",
                    value=(
                        dispatch.data_entrega.isoformat(sep=" ", timespec="minutes")
                        if dispatch.data_entrega
                        else ""
                    ),
                    disabled=True,
                )
                st.text_input(
                    "ID motorista",
                    value=(
                        ""
                        if dispatch.id_funcionario is None
                        else str(dispatch.id_funcionario)
                    ),
                    disabled=True,
                )
                st.text_input(
                    "Motorista", value=dispatch.motorista_nome or "", disabled=True
                )
                st.text_area(
                    "Observacoes", value=dispatch.observacoes or "", disabled=True
                )

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, operation_id)
        st.rerun()


@st.dialog("Editar operacao", width="large")
def _edit(scope: str, operation_id: int) -> None:
    try:
        operation = client.get_operation(operation_id)
        loads = client.list_loads(operation_id)
        vehicles = client.list_vehicles_options()
        locations = client.list_locations_options()
        sales = client.list_sales()
        lots = client.list_lots()
        drivers = client.list_drivers()
    except LogisticsApiError as exc:
        st.error(exc.user_message)
        return

    if not vehicles or not locations or not sales:
        st.warning("Veiculo, locais e venda sao obrigatorios.")
        return

    vehicles_by_id = {v.id_veiculo: v for v in vehicles}
    locations_by_id = {loc.id_local_logistico: loc for loc in locations}
    sales_by_id = {s.id_venda: s for s in sales}
    vehicle_ids = list(vehicles_by_id.keys())
    location_ids = list(locations_by_id.keys())
    sale_ids = list(sales_by_id.keys())
    lot_map = {lot_label(lot): lot.id_lote for lot in lots}

    v_idx = vehicle_ids.index(operation.id_veiculo) if operation.id_veiculo in vehicle_ids else 0
    o_idx = location_ids.index(operation.id_origem) if operation.id_origem in location_ids else 0
    d_idx = location_ids.index(operation.id_destino) if operation.id_destino in location_ids else 0
    s_idx = (
        sale_ids.index(operation.id_venda)
        if operation.id_venda is not None and operation.id_venda in sale_ids
        else 0
    )

    editable_loads = operation.status in {
        OperationStatus.ABERTA,
        OperationStatus.EM_ANDAMENTO,
    }
    active = operation.status in {
        OperationStatus.ABERTA,
        OperationStatus.EM_ANDAMENTO,
    }

    tab_op, tab_cargas, tab_pesagens, tab_exp = st.tabs(
        ["Operacao", "Cargas", "Pesagens", "Expedicao"]
    )

    with tab_op:
        id_veiculo = st.selectbox(
            "ID veiculo",
            vehicle_ids,
            index=v_idx,
            format_func=lambda i: vehicles_by_id[i].placa,
        )
        st.caption(f"Tipo: {vehicle_type_label(vehicles_by_id[id_veiculo].tipo)}")
        id_origem = st.selectbox(
            "ID origem",
            location_ids,
            index=o_idx,
            format_func=lambda i: locations_by_id[i].nome,
        )
        id_destino = st.selectbox(
            "ID destino",
            location_ids,
            index=d_idx,
            format_func=lambda i: locations_by_id[i].nome,
        )
        id_venda = st.selectbox(
            "Venda",
            sale_ids,
            index=s_idx,
            format_func=lambda i: sale_label(sales_by_id[i]),
        )
        _sale_captions(sales_by_id, id_venda)

        status_values = list(OperationStatus)
        status_labels = [OPERATION_STATUS_LABELS[s] for s in status_values]
        status_label = st.selectbox(
            "Status",
            status_labels,
            index=status_values.index(operation.status),
        )
        st.caption(
            "Status gerencial: Aberta → Em andamento (cargas/saida) → "
            "Concluida (entrega) / Cancelada. A expedicao detalha a fase da carga."
        )

        if st.button("Salvar operacao", type="primary", key=f"save_op_{operation_id}"):
            try:
                if id_origem == id_destino:
                    raise ValueError("Origem e destino devem ser diferentes.")
                client.update_operation(
                    operation_id,
                    OperationUpdateSchema(
                        id_veiculo=id_veiculo,
                        id_origem=id_origem,
                        id_destino=id_destino,
                        id_venda=id_venda,
                        status=status_values[status_labels.index(status_label)],
                    ),
                )
                st.toast("Operacao atualizada.")
                clear_dialog_state(scope, operation_id)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except LogisticsApiError as exc:
                st.error(exc.user_message)

    with tab_cargas:
        st.caption("Adicione ou remova cargas. Salve para registrar as alteracoes.")
        loads_df = None
        if editable_loads and lots:
            loads_df = loads_data_editor(
                state_key=f"edit_operation_loads_{operation_id}",
                editor_key=f"edit_operation_loads_editor_{operation_id}",
                lots=lots,
                initial_loads=loads,
                with_ids=True,
            )
            if st.button(
                "Salvar cargas", type="primary", key=f"save_loads_{operation_id}"
            ):
                try:
                    persist_load_rows(
                        client,
                        operation_id,
                        original_loads=loads,
                        rows=loads_df,
                        lot_map=lot_map,
                    )
                    st.toast("Cargas atualizadas.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
                except LogisticsApiError as exc:
                    st.error(exc.user_message)
        else:
            if not editable_loads:
                st.info(
                    "Cargas so podem ser alteradas com operacao Aberta ou Em andamento."
                )
            st.dataframe(loads_view_df(loads), hide_index=True, column_config=loads_view_column_config())

    with tab_pesagens:
        if not loads:
            st.info("Adicione cargas na aba Cargas antes de registrar pesagens.")
        else:
            load_ids = [load.id_carga for load in loads]
            loads_by_id = {load.id_carga: load for load in loads}
            id_carga = st.selectbox(
                "ID carga",
                load_ids,
                format_func=str,
                key=f"edit_pesagem_load_{operation_id}",
            )
            load = loads_by_id[id_carga]
            st.caption(f"Codigo lote: {load.lote_codigo or ''}")
            if load.produto_nome:
                st.caption(f"Produto: {load.produto_nome}")
            try:
                weighings = client.list_weighings(operation_id, id_carga)
            except LogisticsApiError as exc:
                st.error(exc.user_message)
                return
            st.markdown("##### Historico")
            st.dataframe(
                weighings_view_df(weighings),
                hide_index=True,
                column_config=weighings_view_column_config(),
            )
            if active:
                st.markdown("##### Registrar pesagem")
                peso = st.number_input(
                    "Peso registrado",
                    min_value=0.0,
                    step=0.01,
                    key=f"peso_{operation_id}_{id_carga}",
                )
                if st.button(
                    "Registrar pesagem",
                    type="primary",
                    key=f"add_peso_{operation_id}_{id_carga}",
                ):
                    try:
                        client.add_weighing(
                            operation_id,
                            id_carga,
                            WeighingCreateSchema(
                                peso_registrado=peso if peso > 0 else None,
                                data_pesagem=datetime.now(),
                            ),
                        )
                        st.toast("Pesagem registrada.")
                        st.rerun()
                    except LogisticsApiError as exc:
                        st.error(exc.user_message)
            else:
                st.info(
                    "Pesagens so podem ser registradas com operacao Aberta ou Em andamento."
                )

    with tab_exp:
        if not loads:
            st.info("Adicione cargas na aba Cargas antes de informar a expedicao.")
        else:
            load_ids = [load.id_carga for load in loads]
            id_carga = st.selectbox(
                "ID carga",
                load_ids,
                format_func=str,
                key=f"edit_exp_load_{operation_id}",
            )
            try:
                dispatch = client.get_dispatch(operation_id, id_carga)
            except LogisticsApiError as exc:
                st.error(exc.user_message)
                return

            st.markdown("##### Expedicao")
            st.caption(
                "Operacao (gerencial) × Expedicao (operacional): "
                "carga → Em andamento / Em preparacao; saida → Em andamento / Expedida; "
                "entrega → Concluida / Entregue; cancelamento → Cancelada / Cancelada."
            )
            if dispatch is None:
                status_atual = DISPATCH_STATUS_LABELS[DispatchStatus.PENDENTE]
            else:
                status_atual = DISPATCH_STATUS_LABELS.get(
                    dispatch.status, dispatch.status.value
                )
            st.text_input("Status", value=status_atual, disabled=True)

            if not active:
                st.info(
                    "Expedicao so pode ser alterada com operacao Aberta ou Em andamento."
                )
                if dispatch is not None:
                    st.text_input(
                        "Data saida",
                        value=(
                            dispatch.data_saida.date().isoformat()
                            if dispatch.data_saida
                            else ""
                        ),
                        disabled=True,
                    )
                    st.text_input(
                        "Data chegada prevista",
                        value=(
                            dispatch.data_chegada_prevista.date().isoformat()
                            if dispatch.data_chegada_prevista
                            else ""
                        ),
                        disabled=True,
                    )
                    st.text_input(
                        "Data entrega",
                        value=(
                            dispatch.data_entrega.date().isoformat()
                            if dispatch.data_entrega
                            else ""
                        ),
                        disabled=True,
                    )
                    st.text_input(
                        "ID motorista",
                        value=(
                            ""
                            if dispatch.id_funcionario is None
                            else str(dispatch.id_funcionario)
                        ),
                        disabled=True,
                    )
                    st.text_input(
                        "Motorista",
                        value=dispatch.motorista_nome or "",
                        disabled=True,
                    )
                    st.text_area(
                        "Observacoes",
                        value=dispatch.observacoes or "",
                        disabled=True,
                    )
            else:
                data_saida = _optional_datetime(
                    label="Data saida",
                    key=f"exp_saida_{operation_id}_{id_carga}",
                    current=dispatch.data_saida if dispatch else None,
                    enabled_label="Informar data de saida",
                )
                data_chegada = _optional_datetime(
                    label="Data chegada prevista",
                    key=f"exp_chegada_{operation_id}_{id_carga}",
                    current=dispatch.data_chegada_prevista if dispatch else None,
                    enabled_label="Informar chegada prevista",
                )
                data_entrega = _optional_datetime(
                    label="Data entrega",
                    key=f"exp_entrega_{operation_id}_{id_carga}",
                    current=dispatch.data_entrega if dispatch else None,
                    enabled_label="Informar data de entrega",
                )
                id_funcionario = _driver_select(
                    key=f"exp_motorista_{operation_id}_{id_carga}",
                    current_id=dispatch.id_funcionario if dispatch else None,
                    drivers=drivers,
                )
                observacoes = st.text_area(
                    "Observacoes",
                    value=(dispatch.observacoes or "") if dispatch else "",
                    key=f"exp_obs_{operation_id}_{id_carga}",
                )
                if st.button(
                    "Salvar expedicao",
                    type="primary",
                    key=f"save_exp_{operation_id}_{id_carga}",
                ):
                    try:
                        body = dict(
                            data_saida=data_saida,
                            data_chegada_prevista=data_chegada,
                            data_entrega=data_entrega,
                            id_funcionario=id_funcionario,
                            observacoes=observacoes.strip() or None,
                        )
                        if dispatch is None:
                            client.create_dispatch(
                                operation_id,
                                id_carga,
                                DispatchCreateSchema(**body),
                            )
                        else:
                            client.update_dispatch(
                                operation_id,
                                id_carga,
                                DispatchUpdateSchema(**body),
                            )
                        st.toast("Expedicao atualizada.")
                        st.rerun()
                    except LogisticsApiError as exc:
                        st.error(exc.user_message)

    if st.button("Fechar", use_container_width=True, key=f"close_edit_{operation_id}"):
        clear_dialog_state(scope, operation_id)
        st.rerun()


@st.dialog("Excluir operacao")
def _delete(scope: str, operation_id: int) -> None:
    st.write(
        f"Confirma excluir a operacao #{operation_id}? "
        "Cargas, pesagens e expedicoes vinculadas tambem serao removidas."
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Excluir", type="primary", use_container_width=True):
            try:
                client.delete_operation(operation_id)
                st.toast("Operacao excluida.")
                clear_dialog_state(scope, operation_id)
                st.rerun()
            except LogisticsApiError as exc:
                st.error(exc.user_message)
    with c2:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state(scope, operation_id)
            st.rerun()
