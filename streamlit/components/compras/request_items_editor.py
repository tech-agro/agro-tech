"""Request-items data_editor without price column."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.compras.schemas.lookups import ProductOptionSchema
from components.compras.formatters import product_label, product_unit
from components.compras.items_editor import (
    COL_PRODUCT,
    COL_PRODUCT_ID,
    COL_QTY,
    COL_UNIT,
    derived_differ,
    empty_items_df,
    normalize_editor_df,
    parse_product_id,
    row_has_product,
    sync_product_fields,
)
from components.shared.formatters import is_blank

REQUEST_ITEM_COLUMNS = [COL_PRODUCT_ID, COL_PRODUCT, COL_QTY, COL_UNIT]


def request_items_data_editor(
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
    id_col = "id_item"

    if init_flag not in st.session_state:
        if initial_items:
            rows = []
            for item in initial_items:
                product = next(
                    (p for p in products if p.id_produto == item.id_produto), None
                )
                row = {
                    COL_PRODUCT_ID: item.id_produto,
                    COL_PRODUCT: product_label(product) if product else item.produto_nome,
                    COL_QTY: float(item.quantidade),
                    COL_UNIT: product_unit(product) if product else (item.unidade_sigla or ""),
                }
                if with_ids:
                    row = {id_col: item.id_item, **row}
                rows.append(row)
            st.session_state[state_key] = normalize_editor_df(
                pd.DataFrame(rows), with_ids=with_ids
            )
        else:
            st.session_state[state_key] = empty_items_df(with_ids=with_ids)
        st.session_state[prev_key] = st.session_state[state_key].copy()
        st.session_state[init_flag] = True

    base = normalize_editor_df(st.session_state[state_key], with_ids=with_ids)
    st.session_state[state_key] = base

    column_config = {
        COL_PRODUCT_ID: st.column_config.NumberColumn("ID produto", step=1, format="%d"),
        COL_PRODUCT: st.column_config.SelectboxColumn(
            "Produto", options=product_labels, required=False
        ),
        COL_QTY: st.column_config.NumberColumn(
            "Quantidade", min_value=0.01, step=0.01, format="%.2f"
        ),
        COL_UNIT: st.column_config.TextColumn("Unidade de medida", disabled=True),
    }
    disabled_cols = [COL_UNIT]
    if with_ids:
        disabled_cols = [id_col, COL_UNIT]

    edited = st.data_editor(
        base,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        disabled=disabled_cols,
        key=editor_key,
        column_order=REQUEST_ITEM_COLUMNS,
        column_config=column_config,
    )
    edited = normalize_editor_df(edited, with_ids=with_ids)
    previous = st.session_state.get(prev_key)
    synced = sync_product_fields(
        edited, products, previous if isinstance(previous, pd.DataFrame) else None, with_ids=with_ids
    )
    st.session_state[prev_key] = synced.copy()
    if derived_differ(edited, synced):
        st.session_state[state_key] = synced
        st.session_state.pop(editor_key, None)
        st.rerun()
    return synced


def request_rows_to_items(rows: pd.DataFrame, product_map: dict[str, int]):
    from app.compras.schemas.purchase_request_item import PurchaseRequestItemCreateSchema
    from components.compras.items_editor import resolve_product_id

    clean = normalize_editor_df(rows.dropna(how="all"), with_ids=False)
    clean = clean[clean.apply(row_has_product, axis=1)]
    if clean.empty:
        raise ValueError("Informe pelo menos um item na solicitacao.")
    valid_ids = set(product_map.values())
    itens = []
    for _, row in clean.iterrows():
        product_id = resolve_product_id(row, product_map)
        if product_id not in valid_ids:
            raise ValueError(f"Produto invalido na grade: ID {product_id}")
        itens.append(
            PurchaseRequestItemCreateSchema(
                id_produto=product_id,
                quantidade=float(row[COL_QTY]),
            )
        )
    return itens
