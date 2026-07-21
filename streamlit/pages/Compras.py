"""Compras — CRUD padrao: tabela + Novo + Ver/Editar/Excluir."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from app.compras.enum import OrderStatus
from app.compras.schemas.lookups import ProductOptionSchema, SupplierOptionSchema
from app.compras.schemas.order import OrderUpdateSchema
from app.compras.schemas.order_item import OrderItemCreateSchema, OrderItemUpdateSchema
from app.compras.streamlit_client import PurchasesClient
from app.ui.screens import (
    crud_toolbar,
    data_table,
    filter_dataframe,
    row_actions,
    setup_page,
    toast_error,
    toast_ok,
)

setup_page("Compras", "Gestao de pedidos de compra.")

STATUS_LABELS = {
    OrderStatus.ABERTO: "Aberto",
    OrderStatus.APROVADO: "Aprovado",
    OrderStatus.PARCIALMENTE_ATENDIDO: "Parcialmente atendido",
    OrderStatus.ATENDIDO: "Atendido",
    OrderStatus.CANCELADO: "Cancelado",
}

# Chaves internas do editor (sem espaco) — labels em portugues no column_config.
COL_ITEM_ID = "id_item"
COL_PRODUCT_ID = "id_produto"
COL_PRODUCT = "produto"
COL_QTY = "quantidade"
COL_UNIT = "unidade"
COL_PRICE = "valor_unitario"

ITEM_COLUMNS = [COL_PRODUCT_ID, COL_PRODUCT, COL_QTY, COL_UNIT, COL_PRICE]
ITEM_COLUMNS_EDIT = [COL_ITEM_ID, *ITEM_COLUMNS]
DIALOG_KEY = "compras_dialog"


def _client() -> PurchasesClient:
    return PurchasesClient()


def _product_unit(product: ProductOptionSchema) -> str:
    return product.unidade_sigla.value


def _product_label(product: ProductOptionSchema) -> str:
    return product.nome


def _supplier_label(supplier: SupplierOptionSchema) -> str:
    if supplier.categoria:
        return f"{supplier.nome} — {supplier.categoria}"
    return supplier.nome


def _money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, (pd.Series, pd.DataFrame, list, tuple, dict)):
        return True
    try:
        result = pd.isna(value)
    except (ValueError, TypeError):
        return False
    if isinstance(result, (pd.Series, pd.DataFrame)):
        return True
    return bool(result)


def _clear_dialog_state(order_id: int | None = None) -> None:
    st.session_state.pop(DIALOG_KEY, None)
    for key in (
        "new_order_items",
        "new_order_items_editor",
        "_init_new_order_items_editor",
        "new_order_items_prev",
    ):
        st.session_state.pop(key, None)
    if order_id is not None:
        st.session_state.pop(f"edit_order_items_{order_id}", None)
        st.session_state.pop(f"edit_order_items_editor_{order_id}", None)
        st.session_state.pop(f"_init_edit_order_items_editor_{order_id}", None)
        st.session_state.pop(f"edit_order_items_{order_id}_prev", None)


def _open_dialog(kind: str, order_id: int | None = None) -> None:
    current = st.session_state.get(DIALOG_KEY)
    target = (kind, order_id)
    if current != target:
        if kind == "new":
            for key in (
                "new_order_items",
                "new_order_items_editor",
                "_init_new_order_items_editor",
                "new_order_items_prev",
            ):
                st.session_state.pop(key, None)
        if kind == "edit" and order_id is not None:
            st.session_state.pop(f"edit_order_items_{order_id}", None)
            st.session_state.pop(f"edit_order_items_editor_{order_id}", None)
            st.session_state.pop(f"_init_edit_order_items_editor_{order_id}", None)
            st.session_state.pop(f"edit_order_items_{order_id}_prev", None)
    st.session_state[DIALOG_KEY] = target


def _orders_df(orders) -> pd.DataFrame:
    if not orders:
        return pd.DataFrame(columns=["ID", "Fornecedor", "Data", "Status"])
    return pd.DataFrame(
        [
            {
                "ID": o.id_pedido,
                "Fornecedor": o.fornecedor_nome or f"#{o.id_fornecedor}",
                "Data": o.data_pedido.isoformat() if o.data_pedido else "",
                "Status": STATUS_LABELS.get(o.status, o.status.value),
            }
            for o in orders
        ]
    )


def _items_view_df(items) -> pd.DataFrame:
    columns = [
        "ID produto",
        "Produto",
        "Quantidade",
        "Unidade de medida",
        "Valor unitario",
        "Subtotal",
    ]
    if not items:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID produto": i.id_produto,
                "Produto": i.produto_nome or f"#{i.id_produto}",
                "Quantidade": float(i.quantidade),
                "Unidade de medida": i.unidade_sigla.value if i.unidade_sigla else "—",
                "Valor unitario": float(i.valor_unitario),
                "Subtotal": round(float(i.quantidade) * float(i.valor_unitario), 2),
            }
            for i in items
        ]
    )


def _empty_items_df(*, with_ids: bool) -> pd.DataFrame:
    data: dict[str, pd.Series] = {
        COL_PRODUCT_ID: pd.Series(dtype="Int64"),
        COL_PRODUCT: pd.Series(dtype="string"),
        COL_QTY: pd.Series(dtype="Float64"),
        COL_UNIT: pd.Series(dtype="string"),
        COL_PRICE: pd.Series(dtype="Float64"),
    }
    if with_ids:
        data = {COL_ITEM_ID: pd.Series(dtype="Int64"), **data}
    return pd.DataFrame(data)


def _normalize_editor_df(df: pd.DataFrame, *, with_ids: bool) -> pd.DataFrame:
    """Remove indice/colunas fantasmas e garante o schema do editor."""
    clean = df.copy()
    clean = clean.reset_index(drop=True)
    # Remove colunas sem nome ou automaticas do indice
    drop_cols = [
        c
        for c in clean.columns
        if c is None
        or str(c).startswith("Unnamed")
        or str(c).strip() == ""
        or c == "index"
    ]
    if drop_cols:
        clean = clean.drop(columns=drop_cols, errors="ignore")

    expected = ITEM_COLUMNS_EDIT if with_ids else ITEM_COLUMNS
    n = len(clean)
    for col in expected:
        if col not in clean.columns:
            if col in (COL_PRODUCT_ID, COL_ITEM_ID):
                clean[col] = pd.Series([pd.NA] * n, dtype="Int64")
            elif col in (COL_QTY, COL_PRICE):
                clean[col] = pd.Series([pd.NA] * n, dtype="Float64")
            else:
                clean[col] = pd.Series([pd.NA] * n, dtype="string")
        else:
            if col in (COL_PRODUCT_ID, COL_ITEM_ID):
                clean[col] = pd.to_numeric(clean[col], errors="coerce").astype("Int64")
            elif col in (COL_QTY, COL_PRICE):
                clean[col] = pd.to_numeric(clean[col], errors="coerce").astype("Float64")
            else:
                clean[col] = clean[col].astype("string")
    return clean.loc[:, expected]


def _label_for_item(item, products: list[ProductOptionSchema], labels: list[str]) -> str:
    for product in products:
        if product.id_produto == item.id_produto:
            return _product_label(product)
    if item.produto_nome and item.produto_nome in labels:
        return item.produto_nome
    return labels[0] if labels else (item.produto_nome or "")


def _items_editor_df(
    items,
    products: list[ProductOptionSchema],
    *,
    with_ids: bool,
) -> pd.DataFrame:
    if not items:
        return _empty_items_df(with_ids=with_ids)

    labels = [_product_label(p) for p in products]
    rows = []
    for item in items:
        label = _label_for_item(item, products, labels)
        product = next((p for p in products if p.id_produto == item.id_produto), None)
        row = {
            COL_PRODUCT_ID: item.id_produto,
            COL_PRODUCT: label,
            COL_QTY: float(item.quantidade),
            COL_UNIT: _product_unit(product)
            if product
            else (item.unidade_sigla.value if item.unidade_sigla else ""),
            COL_PRICE: float(item.valor_unitario),
        }
        if with_ids:
            row = {COL_ITEM_ID: item.id_item, **row}
        rows.append(row)
    return _normalize_editor_df(pd.DataFrame(rows), with_ids=with_ids)


def _parse_product_id(value) -> int | None:
    if _is_blank(value) or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _sync_product_fields(
    df: pd.DataFrame,
    products: list[ProductOptionSchema],
    previous: pd.DataFrame | None,
    *,
    with_ids: bool,
) -> pd.DataFrame:
    """Preenche ID/nome/unidade. Se o ID mudou, prioriza ID; senao, o nome."""
    synced = _normalize_editor_df(df, with_ids=with_ids)
    by_name = {_product_label(p): p for p in products}
    by_id = {p.id_produto: p for p in products}
    prev = (
        _normalize_editor_df(previous, with_ids=with_ids)
        if isinstance(previous, pd.DataFrame)
        else None
    )

    for idx in synced.index:
        name_raw = synced.at[idx, COL_PRODUCT]
        name = None if _is_blank(name_raw) else str(name_raw).strip()
        product_id = _parse_product_id(synced.at[idx, COL_PRODUCT_ID])

        prev_id = None
        prev_name = None
        if prev is not None and idx in prev.index:
            prev_id = _parse_product_id(prev.at[idx, COL_PRODUCT_ID])
            prev_name_raw = prev.at[idx, COL_PRODUCT]
            prev_name = None if _is_blank(prev_name_raw) else str(prev_name_raw).strip()

        product: ProductOptionSchema | None = None
        if product_id is not None and product_id != prev_id and product_id in by_id:
            product = by_id[product_id]
        elif name and name != prev_name and name in by_name:
            product = by_name[name]
        elif name and name in by_name:
            product = by_name[name]
        elif product_id is not None and product_id in by_id:
            product = by_id[product_id]

        if product is None:
            synced.at[idx, COL_UNIT] = ""
            continue

        synced.at[idx, COL_PRODUCT_ID] = product.id_produto
        synced.at[idx, COL_PRODUCT] = _product_label(product)
        synced.at[idx, COL_UNIT] = _product_unit(product)

    return _normalize_editor_df(synced, with_ids=with_ids)


def _derived_differ(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    for col in (COL_PRODUCT_ID, COL_PRODUCT, COL_UNIT):
        if col not in left.columns or col not in right.columns:
            return True
        a = left[col].astype("string").fillna("").tolist()
        b = right[col].astype("string").fillna("").tolist()
        if a != b:
            return True
    return False


def _items_data_editor(
    *,
    state_key: str,
    editor_key: str,
    products: list[ProductOptionSchema],
    initial_items=None,
    with_ids: bool = False,
) -> pd.DataFrame:
    product_labels = [_product_label(p) for p in products]
    init_flag = f"_init_{editor_key}"
    prev_key = f"{state_key}_prev"

    if init_flag not in st.session_state:
        st.session_state[state_key] = _items_editor_df(
            initial_items or [], products, with_ids=with_ids
        )
        st.session_state[prev_key] = st.session_state[state_key].copy()
        st.session_state[init_flag] = True

    base = _normalize_editor_df(st.session_state[state_key], with_ids=with_ids)
    st.session_state[state_key] = base

    column_config = {
        COL_PRODUCT_ID: st.column_config.NumberColumn(
            "ID produto",
            required=False,
            min_value=1,
            step=1,
            format="%d",
            width="small",
            help="Informe o ID do produto se souber; o nome e a unidade preenchem sozinhos.",
        ),
        COL_PRODUCT: st.column_config.SelectboxColumn(
            "Produto",
            options=product_labels,
            required=False,
        ),
        COL_QTY: st.column_config.NumberColumn(
            "Quantidade",
            required=False,
            min_value=0.01,
            step=0.01,
            format="%.2f",
        ),
        COL_UNIT: st.column_config.TextColumn("Unidade de medida", disabled=True),
        COL_PRICE: st.column_config.NumberColumn(
            "Valor unitario",
            required=False,
            min_value=0.0,
            step=0.01,
            format="%.2f",
        ),
    }
    column_order = list(ITEM_COLUMNS)
    disabled_cols = [COL_UNIT]
    if with_ids:
        column_order = list(ITEM_COLUMNS_EDIT)
        disabled_cols = [COL_ITEM_ID, COL_UNIT]
        column_config[COL_ITEM_ID] = st.column_config.NumberColumn(
            "ID item", disabled=True, width="small", format="%d"
        )

    edited = st.data_editor(
        base,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        disabled=disabled_cols,
        key=editor_key,
        column_order=column_order,
        column_config=column_config,
    )
    edited = _normalize_editor_df(edited, with_ids=with_ids)

    previous = st.session_state.get(prev_key)
    synced = _sync_product_fields(
        edited,
        products,
        previous if isinstance(previous, pd.DataFrame) else None,
        with_ids=with_ids,
    )
    st.session_state[prev_key] = synced.copy()

    if _derived_differ(edited, synced):
        st.session_state[state_key] = synced
        st.session_state.pop(editor_key, None)
        st.rerun()

    total = 0.0
    for _, row in synced.iterrows():
        if _is_blank(row[COL_PRODUCT]) and _parse_product_id(row[COL_PRODUCT_ID]) is None:
            continue
        try:
            total += float(row[COL_QTY]) * float(row[COL_PRICE])
        except (TypeError, ValueError):
            continue
    st.caption(f"Total: {_money(total)}")
    return synced


def _row_has_product(row) -> bool:
    return not _is_blank(row.get(COL_PRODUCT)) or _parse_product_id(row.get(COL_PRODUCT_ID)) is not None


def _resolve_product_id(row, product_map: dict[str, int]) -> int:
    product_id = _parse_product_id(row.get(COL_PRODUCT_ID))
    if product_id is not None:
        return product_id
    product_name = row.get(COL_PRODUCT)
    if not _is_blank(product_name):
        name = str(product_name).strip()
        if name in product_map:
            return product_map[name]
    raise ValueError("Informe o ID ou o nome do produto em cada item.")


def _persist_item_rows(
    order_id: int,
    *,
    original_items,
    rows: pd.DataFrame,
    product_map: dict[str, int],
) -> None:
    clean = _normalize_editor_df(rows.dropna(how="all"), with_ids=True)
    clean = clean[clean.apply(_row_has_product, axis=1)]
    if clean.empty:
        raise ValueError("Informe pelo menos um item no pedido.")

    original_by_id = {i.id_item: i for i in original_items}
    kept_ids: set[int] = set()
    client = _client()
    valid_ids = set(product_map.values())

    for _, row in clean.iterrows():
        product_id = _resolve_product_id(row, product_map)
        if product_id not in valid_ids:
            raise ValueError(f"Produto invalido na grade: ID {product_id}")
        qty = float(row[COL_QTY])
        price = float(row[COL_PRICE])
        raw_id = row[COL_ITEM_ID] if COL_ITEM_ID in row.index else pd.NA

        if _is_blank(raw_id) or raw_id == "":
            client.add_item(
                order_id,
                id_produto=product_id,
                quantidade=qty,
                valor_unitario=price,
            )
            continue

        item_id = int(raw_id)
        original = original_by_id.get(item_id)
        if original is None or original.id_produto != product_id:
            client.add_item(
                order_id,
                id_produto=product_id,
                quantidade=qty,
                valor_unitario=price,
            )
            continue

        client.update_item(
            order_id,
            item_id,
            OrderItemUpdateSchema(quantidade=qty, valor_unitario=price),
        )
        kept_ids.add(item_id)

    for item_id in set(original_by_id) - kept_ids:
        client.delete_item(order_id, item_id)


@st.dialog("Novo pedido", width="large")
def _dialog_new_order(
    suppliers: list[SupplierOptionSchema],
    products: list[ProductOptionSchema],
) -> None:
    if not suppliers or not products:
        st.warning("Cadastre ao menos um fornecedor e um produto para criar pedidos.")
        return

    supplier_map = {_supplier_label(s): s.id_fornecedor for s in suppliers}
    product_map = {_product_label(p): p.id_produto for p in products}

    st.caption("Informe fornecedor e pelo menos um item.")
    supplier_label = st.selectbox("Fornecedor", list(supplier_map.keys()))

    st.markdown("##### Itens")
    st.caption(
        "Clique em + para adicionar. Informe o ID do produto ou escolha o nome; "
        "a unidade preenche sozinha e nao e editavel."
    )
    items_df = _items_data_editor(
        state_key="new_order_items",
        editor_key="new_order_items_editor",
        products=products,
        with_ids=False,
    )

    col_cancel, _, col_save = st.columns([1, 3, 1])
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            _clear_dialog_state()
            st.rerun()
    with col_save:
        if st.button("Criar", type="primary", use_container_width=True):
            rows = _normalize_editor_df(items_df.dropna(how="all"), with_ids=False)
            rows = rows[rows.apply(_row_has_product, axis=1)]
            if rows.empty:
                st.toast("Erro: Informe pelo menos um item no pedido.")
                return
            try:
                valid_ids = set(product_map.values())
                itens = []
                for _, row in rows.iterrows():
                    product_id = _resolve_product_id(row, product_map)
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
                    id_fornecedor=supplier_map[str(supplier_label)],
                    data_pedido=date.today(),
                    status=OrderStatus.ABERTO,
                    itens=itens,
                )
                _clear_dialog_state()
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
    st.dataframe(_items_view_df(items), use_container_width=True, hide_index=True)
    total = sum(float(i.quantidade) * float(i.valor_unitario) for i in items)
    st.caption(f"Total: {_money(total)}")

    _, col_close = st.columns([4, 1])
    with col_close:
        if st.button("Fechar", use_container_width=True):
            _clear_dialog_state()
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

    supplier_map = {_supplier_label(s): s.id_fornecedor for s in suppliers}
    id_to_label = {s.id_fornecedor: _supplier_label(s) for s in suppliers}
    default_label = id_to_label.get(order.id_fornecedor, list(supplier_map.keys())[0])
    supplier_labels = list(supplier_map.keys())
    status_labels = [STATUS_LABELS[s] for s in OrderStatus]
    status_values = list(OrderStatus)
    product_map = {_product_label(p): p.id_produto for p in products}
    editable_items = order.status == OrderStatus.ABERTO
    state_key = f"edit_order_items_{order_id}"

    st.caption(f"Pedido #{order.id_pedido}")
    h1, h2 = st.columns(2)
    with h1:
        supplier_label = st.selectbox(
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
        items_df = _items_data_editor(
            state_key=state_key,
            editor_key=f"edit_order_items_editor_{order_id}",
            products=products,
            initial_items=items,
            with_ids=True,
        )
    else:
        st.info("Itens so podem ser alterados com pedido Aberto.")
        st.dataframe(_items_view_df(items), use_container_width=True, hide_index=True)
        total = sum(float(i.quantidade) * float(i.valor_unitario) for i in items)
        st.caption(f"Total: {_money(total)}")
        items_df = None

    col_cancel, _, col_save = st.columns([1, 3, 1])
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            _clear_dialog_state(order_id)
            st.rerun()
    with col_save:
        if st.button("Salvar", type="primary", use_container_width=True):
            try:
                if editable_items and items_df is not None:
                    _persist_item_rows(
                        order_id,
                        original_items=items,
                        rows=items_df,
                        product_map=product_map,
                    )
                _client().update_order(
                    order.id_pedido,
                    OrderUpdateSchema(
                        id_fornecedor=supplier_map[supplier_label],
                        status=status_values[status_labels.index(status_label)],
                    ),
                )
                _clear_dialog_state(order_id)
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
                _clear_dialog_state(order_id)
                toast_ok("Pedido excluido.")
                st.rerun()
            except Exception as exc:
                toast_error(exc)
    with c2:
        if st.button("Cancelar", use_container_width=True):
            _clear_dialog_state(order_id)
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
    _open_dialog("new")

df = filter_dataframe(_orders_df(orders), query)
selected = data_table(df, key="compras_orders")
action = row_actions(
    key="compras",
    selected_count=len(selected),
    total_count=len(df),
    disabled=not selected,
)

if action == "view" and selected:
    _open_dialog("view", int(selected[0]["ID"]))
elif action == "edit" and selected:
    _open_dialog("edit", int(selected[0]["ID"]))
elif action == "delete" and selected:
    _open_dialog("delete", int(selected[0]["ID"]))

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
