"""Order-items data_editor and persistence helpers for purchases."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.compras.schemas.lookups import ProductOptionSchema
from app.compras.schemas.order_item import OrderItemUpdateSchema
from components.compras.formatters import product_label, product_unit
from components.shared.formatters import format_money, is_blank
from services.compras_client import PurchasesClient

# Internal editor keys (no spaces) — Portuguese labels live in column_config.
COL_ITEM_ID = "id_item"
COL_PRODUCT_ID = "id_produto"
COL_PRODUCT = "produto"
COL_QTY = "quantidade"
COL_UNIT = "unidade"
COL_PRICE = "valor_unitario"

ITEM_COLUMNS = [COL_PRODUCT_ID, COL_PRODUCT, COL_QTY, COL_UNIT, COL_PRICE]
ITEM_COLUMNS_EDIT = [COL_ITEM_ID, *ITEM_COLUMNS]


def empty_items_df(*, with_ids: bool) -> pd.DataFrame:
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


def normalize_editor_df(df: pd.DataFrame, *, with_ids: bool) -> pd.DataFrame:
    """Remove phantom index/columns and enforce the editor schema."""
    clean = df.copy()
    clean = clean.reset_index(drop=True)
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
            return product_label(product)
    if item.produto_nome and item.produto_nome in labels:
        return item.produto_nome
    return labels[0] if labels else (item.produto_nome or "")


def items_editor_df(
    items,
    products: list[ProductOptionSchema],
    *,
    with_ids: bool,
) -> pd.DataFrame:
    if not items:
        return empty_items_df(with_ids=with_ids)

    labels = [product_label(p) for p in products]
    rows = []
    for item in items:
        label = _label_for_item(item, products, labels)
        product = next((p for p in products if p.id_produto == item.id_produto), None)
        row = {
            COL_PRODUCT_ID: item.id_produto,
            COL_PRODUCT: label,
            COL_QTY: float(item.quantidade),
            COL_UNIT: product_unit(product)
            if product
            else (item.unidade_sigla.value if item.unidade_sigla else ""),
            COL_PRICE: float(item.valor_unitario),
        }
        if with_ids:
            row = {COL_ITEM_ID: item.id_item, **row}
        rows.append(row)
    return normalize_editor_df(pd.DataFrame(rows), with_ids=with_ids)


def parse_product_id(value) -> int | None:
    if is_blank(value) or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def sync_product_fields(
    df: pd.DataFrame,
    products: list[ProductOptionSchema],
    previous: pd.DataFrame | None,
    *,
    with_ids: bool,
) -> pd.DataFrame:
    """Fill ID/name/unit. If ID changed, prefer ID; otherwise prefer name."""
    synced = normalize_editor_df(df, with_ids=with_ids)
    by_name = {product_label(p): p for p in products}
    by_id = {p.id_produto: p for p in products}
    prev = (
        normalize_editor_df(previous, with_ids=with_ids)
        if isinstance(previous, pd.DataFrame)
        else None
    )

    for idx in synced.index:
        name_raw = synced.at[idx, COL_PRODUCT]
        name = None if is_blank(name_raw) else str(name_raw).strip()
        product_id = parse_product_id(synced.at[idx, COL_PRODUCT_ID])

        prev_id = None
        prev_name = None
        if prev is not None and idx in prev.index:
            prev_id = parse_product_id(prev.at[idx, COL_PRODUCT_ID])
            prev_name_raw = prev.at[idx, COL_PRODUCT]
            prev_name = None if is_blank(prev_name_raw) else str(prev_name_raw).strip()

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
        synced.at[idx, COL_PRODUCT] = product_label(product)
        synced.at[idx, COL_UNIT] = product_unit(product)

    return normalize_editor_df(synced, with_ids=with_ids)


def derived_differ(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    for col in (COL_PRODUCT_ID, COL_PRODUCT, COL_UNIT):
        if col not in left.columns or col not in right.columns:
            return True
        a = left[col].astype("string").fillna("").tolist()
        b = right[col].astype("string").fillna("").tolist()
        if a != b:
            return True
    return False


def items_data_editor(
    *,
    state_key: str,
    editor_key: str,
    products: list[ProductOptionSchema],
    initial_items=None,
    with_ids: bool = False,
) -> pd.DataFrame:
    product_labels = [product_label(p) for p in products]
    init_flag = f"_init_{editor_key}"
    prev_key = f"{state_key}_prev"

    if init_flag not in st.session_state:
        st.session_state[state_key] = items_editor_df(
            initial_items or [], products, with_ids=with_ids
        )
        st.session_state[prev_key] = st.session_state[state_key].copy()
        st.session_state[init_flag] = True

    base = normalize_editor_df(st.session_state[state_key], with_ids=with_ids)
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
    # id_item fica no DataFrame so para persistencia (update/delete); nao aparece no form.
    if with_ids:
        disabled_cols = [COL_ITEM_ID, COL_UNIT]

    edited = st.data_editor(
        base,
        num_rows="dynamic",
        hide_index=True,
        disabled=disabled_cols,
        key=editor_key,
        column_order=column_order,
        column_config=column_config,
    )
    edited = normalize_editor_df(edited, with_ids=with_ids)

    previous = st.session_state.get(prev_key)
    synced = sync_product_fields(
        edited,
        products,
        previous if isinstance(previous, pd.DataFrame) else None,
        with_ids=with_ids,
    )
    st.session_state[prev_key] = synced.copy()

    if derived_differ(edited, synced):
        st.session_state[state_key] = synced
        st.session_state.pop(editor_key, None)
        st.rerun()

    total = 0.0
    for _, row in synced.iterrows():
        if is_blank(row[COL_PRODUCT]) and parse_product_id(row[COL_PRODUCT_ID]) is None:
            continue
        try:
            total += float(row[COL_QTY]) * float(row[COL_PRICE])
        except (TypeError, ValueError):
            continue
    st.caption(f"Total: {format_money(total)}")
    return synced


def row_has_product(row) -> bool:
    return not is_blank(row.get(COL_PRODUCT)) or parse_product_id(row.get(COL_PRODUCT_ID)) is not None


def resolve_product_id(row, product_map: dict[str, int]) -> int:
    product_id = parse_product_id(row.get(COL_PRODUCT_ID))
    if product_id is not None:
        return product_id
    product_name = row.get(COL_PRODUCT)
    if not is_blank(product_name):
        name = str(product_name).strip()
        if name in product_map:
            return product_map[name]
    raise ValueError("Informe o ID ou o nome do produto em cada item.")


def persist_item_rows(
    client: PurchasesClient,
    order_id: int,
    *,
    original_items,
    rows: pd.DataFrame,
    product_map: dict[str, int],
) -> None:
    clean = normalize_editor_df(rows.dropna(how="all"), with_ids=True)
    clean = clean[clean.apply(row_has_product, axis=1)]
    if clean.empty:
        raise ValueError("Informe pelo menos um item no pedido.")

    original_by_id = {i.id_item: i for i in original_items}
    kept_ids: set[int] = set()
    valid_ids = set(product_map.values())

    for _, row in clean.iterrows():
        product_id = resolve_product_id(row, product_map)
        if product_id not in valid_ids:
            raise ValueError(f"Produto invalido na grade: ID {product_id}")
        qty = float(row[COL_QTY])
        price = float(row[COL_PRICE])
        raw_id = row[COL_ITEM_ID] if COL_ITEM_ID in row.index else pd.NA

        if is_blank(raw_id) or raw_id == "":
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
