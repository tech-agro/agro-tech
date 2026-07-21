"""Compras — CRUD padrao: tabela + Novo + Ver/Editar/Excluir."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

# Allow ``components.*`` / ``services.*`` imports (folder is named streamlit/).
_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from app.compras.enum import OrderStatus
from app.compras.schemas.lookups import ProductOptionSchema, SupplierOptionSchema
from app.compras.schemas.order import OrderUpdateSchema
from app.compras.schemas.order_item import OrderItemCreateSchema
from components.compras.dialog_state import DIALOG_KEY, clear_dialog_state, open_dialog
from components.compras.formatters import STATUS_LABELS, product_label, supplier_label
from components.compras.items_editor import (
    COL_PRICE,
    COL_QTY,
    items_data_editor,
    normalize_editor_df,
    persist_item_rows,
    resolve_product_id,
    row_has_product,
)
from components.compras.order_tables import items_view_df, orders_df
from components.shared.formatters import format_money
from components.shared.screens import (
    crud_toolbar,
    data_table,
    filter_dataframe,
    row_actions,
    setup_page,
    toast_error,
    toast_ok,
)
from services.compras_client import PurchasesClient

setup_page("Compras", "Gestao de pedidos de compra.")


def _client() -> PurchasesClient:
    return PurchasesClient()


@st.dialog("Novo pedido", width="large")
def _dialog_new_order(
    suppliers: list[SupplierOptionSchema],
    products: list[ProductOptionSchema],
) -> None:
    if not suppliers or not products:
        st.warning("Cadastre ao menos um fornecedor e um produto para criar pedidos.")
        return

    supplier_map = {supplier_label(s): s.id_fornecedor for s in suppliers}
    product_map = {product_label(p): p.id_produto for p in products}

    st.caption("Informe fornecedor e pelo menos um item.")
    supplier_choice = st.selectbox("Fornecedor", list(supplier_map.keys()))

    st.markdown("##### Itens")
    st.caption(
        "Clique em + para adicionar. Informe o ID do produto ou escolha o nome; "
        "a unidade preenche sozinha e nao e editavel."
    )
    items_df = items_data_editor(
        state_key="new_order_items",
        editor_key="new_order_items_editor",
        products=products,
        with_ids=False,
    )

    col_cancel, _, col_save = st.columns([1, 3, 1])
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state()
            st.rerun()
    with col_save:
        if st.button("Criar", type="primary", use_container_width=True):
            rows = normalize_editor_df(items_df.dropna(how="all"), with_ids=False)
            rows = rows[rows.apply(row_has_product, axis=1)]
            if rows.empty:
                st.toast("Erro: Informe pelo menos um item no pedido.")
                return
            try:
                valid_ids = set(product_map.values())
                itens = []
                for _, row in rows.iterrows():
                    product_id = resolve_product_id(row, product_map)
                    if product_id not in valid_ids:
                        raise ValueError(f"Produto invalido na grade: ID {product_id}")
                    itens.append(
                        OrderItemCreateSchema(
                            id_produto=product_id,
                            quantidade=float(row[COL_QTY]),
                            valor_unitario=float(row[COL_PRICE]),
                        )
                    )
                order = _client().create_order(
                    id_fornecedor=supplier_map[str(supplier_choice)],
                    data_pedido=date.today(),
                    status=OrderStatus.ABERTO,
                    itens=itens,
                )
                clear_dialog_state()
                toast_ok(f"Pedido #{order.id_pedido} criado.")
                st.rerun()
            except ValueError as exc:
                st.toast(f"Erro: {exc}")
            except Exception as exc:
                toast_error(exc)


@st.dialog("Visualizar pedido", width="large")
def _dialog_detail(order_id: int) -> None:
    try:
        order = _client().get_order(order_id)
        items = _client().list_items(order_id)
    except Exception as exc:
        toast_error(exc)
        st.stop()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Pedido", value=f"#{order.id_pedido}", disabled=True)
    with c2:
        st.text_input(
            "Fornecedor",
            value=order.fornecedor_nome or f"#{order.id_fornecedor}",
            disabled=True,
        )
    with c3:
        st.text_input(
            "Status",
            value=STATUS_LABELS.get(order.status, order.status.value),
            disabled=True,
        )
    st.text_input(
        "Data do pedido",
        value=order.data_pedido.isoformat() if order.data_pedido else "—",
        disabled=True,
    )

    st.markdown("##### Itens")
    st.dataframe(items_view_df(items), use_container_width=True, hide_index=True)
    total = sum(float(i.quantidade) * float(i.valor_unitario) for i in items)
    st.caption(f"Total: {format_money(total)}")

    _, col_close = st.columns([4, 1])
    with col_close:
        if st.button("Fechar", use_container_width=True):
            clear_dialog_state()
            st.rerun()


@st.dialog("Editar pedido", width="large")
def _dialog_edit(
    order_id: int,
    suppliers: list[SupplierOptionSchema],
    products: list[ProductOptionSchema],
) -> None:
    try:
        order = _client().get_order(order_id)
        items = _client().list_items(order_id)
    except Exception as exc:
        toast_error(exc)
        st.stop()

    if not suppliers:
        st.warning("Nenhum fornecedor disponivel.")
        return

    supplier_map = {supplier_label(s): s.id_fornecedor for s in suppliers}
    id_to_label = {s.id_fornecedor: supplier_label(s) for s in suppliers}
    default_label = id_to_label.get(order.id_fornecedor, list(supplier_map.keys())[0])
    supplier_labels = list(supplier_map.keys())
    status_labels = [STATUS_LABELS[s] for s in OrderStatus]
    status_values = list(OrderStatus)
    product_map = {product_label(p): p.id_produto for p in products}
    editable_items = order.status == OrderStatus.ABERTO
    state_key = f"edit_order_items_{order_id}"

    st.caption(f"Pedido #{order.id_pedido}")
    h1, h2 = st.columns(2)
    with h1:
        supplier_choice = st.selectbox(
            "Fornecedor",
            supplier_labels,
            index=(
                supplier_labels.index(default_label)
                if default_label in supplier_labels
                else 0
            ),
        )
    with h2:
        st.text_input(
            "Data do pedido",
            value=order.data_pedido.isoformat() if order.data_pedido else "—",
            disabled=True,
        )
    status_label = st.selectbox(
        "Status",
        status_labels,
        index=status_values.index(order.status),
    )
    st.caption(
        "Ao salvar com status Aprovado, a compra e registrada automaticamente."
    )

    st.markdown("##### Itens")
    if editable_items:
        st.caption(
            "Edite as celulas, use + para incluir e o menu da linha para excluir. "
            "Informe o ID do produto ou o nome; unidade nao e editavel."
        )
        items_df = items_data_editor(
            state_key=state_key,
            editor_key=f"edit_order_items_editor_{order_id}",
            products=products,
            initial_items=items,
            with_ids=True,
        )
    else:
        st.info("Itens so podem ser alterados com pedido Aberto.")
        st.dataframe(items_view_df(items), use_container_width=True, hide_index=True)
        total = sum(float(i.quantidade) * float(i.valor_unitario) for i in items)
        st.caption(f"Total: {format_money(total)}")
        items_df = None

    col_cancel, _, col_save = st.columns([1, 3, 1])
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state(order_id)
            st.rerun()
    with col_save:
        if st.button("Salvar", type="primary", use_container_width=True):
            try:
                if editable_items and items_df is not None:
                    persist_item_rows(
                        _client(),
                        order_id,
                        original_items=items,
                        rows=items_df,
                        product_map=product_map,
                    )
                _client().update_order(
                    order.id_pedido,
                    OrderUpdateSchema(
                        id_fornecedor=supplier_map[supplier_choice],
                        status=status_values[status_labels.index(status_label)],
                    ),
                )
                clear_dialog_state(order_id)
                toast_ok("Pedido atualizado.")
                st.rerun()
            except ValueError as exc:
                st.toast(f"Erro: {exc}")
            except Exception as exc:
                toast_error(exc)


@st.dialog("Excluir pedido")
def _dialog_delete(order_id: int) -> None:
    st.write(f"Confirma excluir o pedido #{order_id}?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Excluir", type="primary", use_container_width=True):
            try:
                _client().delete_order(order_id)
                clear_dialog_state(order_id)
                toast_ok("Pedido excluido.")
                st.rerun()
            except Exception as exc:
                toast_error(exc)
    with c2:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state(order_id)
            st.rerun()


try:
    client = _client()
    orders = client.list_orders()
    suppliers = client.list_suppliers()
    products = client.list_products()
except Exception as exc:
    st.error(f"Nao foi possivel carregar os pedidos: {exc}")
    st.stop()

query, new_clicked = crud_toolbar(
    key="compras",
    filter_placeholder="Filtrar pedidos...",
    new_label="Novo",
)
if new_clicked:
    open_dialog("new")

df = filter_dataframe(orders_df(orders), query)
selected = data_table(df, key="compras_orders")
action = row_actions(
    key="compras",
    selected_count=len(selected),
    total_count=len(df),
    disabled=not selected,
)

if action == "view" and selected:
    open_dialog("view", int(selected[0]["ID"]))
elif action == "edit" and selected:
    open_dialog("edit", int(selected[0]["ID"]))
elif action == "delete" and selected:
    open_dialog("delete", int(selected[0]["ID"]))

dialog = st.session_state.get(DIALOG_KEY)
if dialog:
    kind, order_id = dialog
    if kind == "new":
        _dialog_new_order(suppliers, products)
    elif kind == "view" and order_id is not None:
        _dialog_detail(order_id)
    elif kind == "edit" and order_id is not None:
        _dialog_edit(order_id, suppliers, products)
    elif kind == "delete" and order_id is not None:
        _dialog_delete(order_id)
