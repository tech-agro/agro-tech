"""Dialogs for purchase requests (solicitacoes de compra)."""

from __future__ import annotations

from datetime import date

import streamlit as st

from app.compras.enum import PurchaseRequestStatus, PurchaseType
from app.compras.schemas.lookups import (
    FarmOptionSchema,
    MachineTypeOptionSchema,
    ProductOptionSchema,
    SupplierOptionSchema,
)
from app.compras.schemas.purchase_request import PurchaseRequestUpdateSchema
from components.compras.dialog_state import clear_dialog_state, get_dialog, open_dialog
from components.compras.formatters import (
    PURCHASE_TYPE_LABELS,
    REQUEST_STATUS_LABELS,
    product_label,
)
from components.compras.quotation_dialogs import dialog_quotations
from components.compras.request_items_editor import (
    request_items_data_editor,
    request_rows_to_items,
)
from components.compras.request_tables import request_items_view_column_config, request_items_view_df
from components.shared.screens import toast_error, toast_ok
from services.compras_client import PurchasesClient


def _equipment_fields(
    tipo: PurchaseType,
    farms: list[FarmOptionSchema],
    machine_types: list[MachineTypeOptionSchema],
    *,
    default_tipo_maquina: int | None = None,
    default_fazenda: int | None = None,
    default_patrimonio: str | None = None,
) -> tuple[int | None, int | None, str | None]:
    if tipo != PurchaseType.EQUIPAMENTO:
        return None, None, None
    if not farms or not machine_types:
        st.warning("Cadastre fazenda e tipo de maquina para solicitacao de equipamento.")
        return None, None, None
    farm_map = {f.nome: f.id_fazenda for f in farms}
    type_map = {t.descricao: t.id_tipo_maquina for t in machine_types}
    farm_labels = list(farm_map.keys())
    type_labels = list(type_map.keys())
    c1, c2 = st.columns(2)
    with c1:
        tipo_label = st.selectbox(
            "Tipo de maquina",
            type_labels,
            index=(
                type_labels.index(
                    next(
                        t.descricao
                        for t in machine_types
                        if t.id_tipo_maquina == default_tipo_maquina
                    )
                )
                if default_tipo_maquina
                and any(t.id_tipo_maquina == default_tipo_maquina for t in machine_types)
                else 0
            ),
        )
    with c2:
        farm_label = st.selectbox(
            "Fazenda",
            farm_labels,
            index=(
                farm_labels.index(
                    next(f.nome for f in farms if f.id_fazenda == default_fazenda)
                )
                if default_fazenda and any(f.id_fazenda == default_fazenda for f in farms)
                else 0
            ),
        )
    patrimonio = st.text_input("Patrimonio", value=default_patrimonio or "")
    return (
        type_map[tipo_label],
        farm_map[farm_label],
        patrimonio.strip() or None,
    )


@st.dialog("Nova solicitacao", width="large")
def _dialog_new_request(
    client: PurchasesClient,
    products: list[ProductOptionSchema],
    farms: list[FarmOptionSchema],
    machine_types: list[MachineTypeOptionSchema],
) -> None:
    if not products:
        st.warning("Cadastre ao menos um produto.")
        return
    product_map = {product_label(p): p.id_produto for p in products}
    tipo_labels = list(PURCHASE_TYPE_LABELS.values())
    tipo_values = list(PURCHASE_TYPE_LABELS.keys())
    tipo_label = st.selectbox("Tipo de compra", tipo_labels)
    tipo = tipo_values[tipo_labels.index(tipo_label)]
    observacao = st.text_area("Observacao", value="")
    id_tipo_maquina = id_fazenda = patrimonio = None
    if tipo == PurchaseType.EQUIPAMENTO:
        id_tipo_maquina, id_fazenda, patrimonio = _equipment_fields(
            tipo, farms, machine_types
        )
    st.markdown("##### Itens")
    items_df = request_items_data_editor(
        state_key="new_request_items",
        editor_key="new_request_items_editor",
        products=products,
    )
    c1, _, c2 = st.columns([1, 3, 1])
    with c1:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state("solicitacoes")
            st.rerun()
    with c2:
        if st.button("Criar", type="primary", use_container_width=True):
            try:
                itens = request_rows_to_items(items_df, product_map)
                req = client.create_request(
                    tipo_compra=tipo,
                    itens=itens,
                    observacao=observacao or None,
                    id_tipo_maquina=id_tipo_maquina,
                    id_fazenda=id_fazenda,
                    patrimonio=patrimonio,
                    data_solicitacao=date.today(),
                )
                clear_dialog_state("solicitacoes")
                toast_ok(f"Solicitacao #{req.id_solicitacao} criada.")
                st.rerun()
            except ValueError as exc:
                st.toast(f"Erro: {exc}")
            except Exception as exc:
                toast_error(exc)


@st.dialog("Visualizar solicitacao", width="large")
def _dialog_view_request(client: PurchasesClient, request_id: int) -> None:
    try:
        request = client.get_request(request_id)
        items = client.list_request_items(request_id)
    except Exception as exc:
        toast_error(exc)
        st.stop()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Solicitacao", value=f"#{request.id_solicitacao}", disabled=True)
    with c2:
        st.text_input(
            "Status",
            value=REQUEST_STATUS_LABELS.get(request.status, request.status.value),
            disabled=True,
        )
    with c3:
        st.text_input(
            "Tipo",
            value=PURCHASE_TYPE_LABELS.get(request.tipo_compra, request.tipo_compra.value),
            disabled=True,
        )
    st.text_input("Data", value=request.data_solicitacao.isoformat(), disabled=True)
    if request.observacao:
        st.text_area("Observacao", value=request.observacao, disabled=True)
    if request.id_pedido:
        st.info(f"Pedido gerado: #{request.id_pedido}")
    st.markdown("##### Itens")
    st.dataframe(request_items_view_df(items), hide_index=True, column_config=request_items_view_column_config())
    _, col_close = st.columns([4, 1])
    with col_close:
        if st.button("Fechar", use_container_width=True):
            clear_dialog_state("solicitacoes", request_id)
            st.rerun()


@st.dialog("Editar solicitacao", width="large")
def _dialog_edit_request(
    client: PurchasesClient,
    request_id: int,
    products: list[ProductOptionSchema],
    farms: list[FarmOptionSchema],
    machine_types: list[MachineTypeOptionSchema],
) -> None:
    try:
        request = client.get_request(request_id)
        items = client.list_request_items(request_id)
    except Exception as exc:
        toast_error(exc)
        st.stop()

    editable = request.status == PurchaseRequestStatus.RASCUNHO
    status_labels = [REQUEST_STATUS_LABELS[s] for s in PurchaseRequestStatus]
    status_values = list(PurchaseRequestStatus)
    current_status_label = REQUEST_STATUS_LABELS[request.status]

    st.caption(f"Solicitacao #{request.id_solicitacao}")
    observacao = st.text_area("Observacao", value=request.observacao or "")
    status_label = st.selectbox(
        "Status",
        status_labels,
        index=status_values.index(request.status),
    )
    id_tipo_maquina = request.id_tipo_maquina
    id_fazenda = request.id_fazenda
    patrimonio = request.patrimonio
    if request.tipo_compra == PurchaseType.EQUIPAMENTO and editable:
        id_tipo_maquina, id_fazenda, patrimonio = _equipment_fields(
            request.tipo_compra,
            farms,
            machine_types,
            default_tipo_maquina=request.id_tipo_maquina,
            default_fazenda=request.id_fazenda,
            default_patrimonio=request.patrimonio,
        )

    items_df = None
    product_map = {product_label(p): p.id_produto for p in products}
    if editable:
        st.markdown("##### Itens")
        items_df = request_items_data_editor(
            state_key=f"edit_request_items_{request_id}",
            editor_key=f"edit_request_items_editor_{request_id}",
            products=products,
            initial_items=items,
            with_ids=True,
        )
    else:
        st.markdown("##### Itens")
        st.dataframe(request_items_view_df(items), hide_index=True, column_config=request_items_view_column_config())

    c1, c2, c3 = st.columns(3)
    with c1:
        if request.status == PurchaseRequestStatus.RASCUNHO:
            if st.button("Enviar solicitacao", use_container_width=True):
                try:
                    client.update_request(
                        request_id,
                        PurchaseRequestUpdateSchema(status=PurchaseRequestStatus.ENVIADA),
                    )
                    toast_ok("Solicitacao enviada.")
                    clear_dialog_state("solicitacoes", request_id)
                    st.rerun()
                except Exception as exc:
                    toast_error(exc)
    with c2:
        if request.status == PurchaseRequestStatus.ENVIADA:
            if st.button("Aprovar", type="primary", use_container_width=True):
                try:
                    client.update_request(
                        request_id,
                        PurchaseRequestUpdateSchema(status=PurchaseRequestStatus.APROVADA),
                    )
                    toast_ok("Solicitacao aprovada.")
                    clear_dialog_state("solicitacoes", request_id)
                    st.rerun()
                except Exception as exc:
                    toast_error(exc)
    with c3:
        if request.status == PurchaseRequestStatus.ENVIADA:
            if st.button("Rejeitar", use_container_width=True):
                try:
                    client.update_request(
                        request_id,
                        PurchaseRequestUpdateSchema(status=PurchaseRequestStatus.REJEITADA),
                    )
                    toast_ok("Solicitacao rejeitada.")
                    clear_dialog_state("solicitacoes", request_id)
                    st.rerun()
                except Exception as exc:
                    toast_error(exc)

    col_cancel, _, col_save = st.columns([1, 3, 1])
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state("solicitacoes", request_id)
            st.rerun()
    with col_save:
        if st.button("Salvar", type="primary", use_container_width=True):
            try:
                new_status = status_values[status_labels.index(status_label)]
                client.update_request(
                    request_id,
                    PurchaseRequestUpdateSchema(
                        status=new_status,
                        observacao=observacao or None,
                        id_tipo_maquina=id_tipo_maquina,
                        id_fazenda=id_fazenda,
                        patrimonio=patrimonio,
                    ),
                )
                if editable and items_df is not None:
                    new_itens = request_rows_to_items(items_df, product_map)
                    for item_payload in new_itens:
                        client.add_request_item(request_id, item_payload)
                    for item in items:
                        client.delete_request_item(request_id, item.id_item)
                clear_dialog_state("solicitacoes", request_id)
                toast_ok("Solicitacao atualizada.")
                st.rerun()
            except Exception as exc:
                toast_error(exc)


@st.dialog("Excluir solicitacao")
def _dialog_delete_request(client: PurchasesClient, request_id: int) -> None:
    st.write(f"Confirma excluir a solicitacao #{request_id}?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Excluir", type="primary", use_container_width=True):
            try:
                client.delete_request(request_id)
                clear_dialog_state("solicitacoes", request_id)
                toast_ok("Solicitacao excluida.")
                st.rerun()
            except Exception as exc:
                toast_error(exc)
    with c2:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state("solicitacoes", request_id)
            st.rerun()


def render(
    scope: str,
    client: PurchasesClient,
    products: list[ProductOptionSchema],
    farms: list[FarmOptionSchema],
    machine_types: list[MachineTypeOptionSchema],
    suppliers: list[SupplierOptionSchema],
) -> None:
    dialog = get_dialog(scope)
    if not dialog:
        return
    kind, request_id = dialog
    if kind == "new":
        _dialog_new_request(client, products, farms, machine_types)
    elif kind == "view" and request_id is not None:
        _dialog_view_request(client, request_id)
    elif kind == "edit" and request_id is not None:
        _dialog_edit_request(client, request_id, products, farms, machine_types)
    elif kind == "delete" and request_id is not None:
        _dialog_delete_request(client, request_id)
    elif kind == "quote" and request_id is not None:
        dialog_quotations(client, request_id, suppliers, products)
