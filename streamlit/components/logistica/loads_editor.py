"""Load data_editor and persistence helpers for logistics operations."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.logistica.schemas.load import LoadCreateSchema, LoadUpdateSchema
from app.logistica.schemas.lookups import LotOptionSchema
from components.logistica.formatters import lot_label
from components.shared.formatters import is_blank
from services.logistica_client import LogisticsClient

COL_LOAD_ID = "id_carga"
COL_LOT_ID = "id_lote"
COL_LOT = "lote"
COL_QTY = "quantidade"
COL_WEIGHT = "peso_previsto"

LOAD_COLUMNS = [COL_LOT_ID, COL_LOT, COL_QTY, COL_WEIGHT]
LOAD_COLUMNS_EDIT = [COL_LOAD_ID, *LOAD_COLUMNS]


def empty_loads_df(*, with_ids: bool) -> pd.DataFrame:
    data: dict[str, pd.Series] = {
        COL_LOT_ID: pd.Series(dtype="Int64"),
        COL_LOT: pd.Series(dtype="string"),
        COL_QTY: pd.Series(dtype="Float64"),
        COL_WEIGHT: pd.Series(dtype="Float64"),
    }
    if with_ids:
        data = {COL_LOAD_ID: pd.Series(dtype="Int64"), **data}
    return pd.DataFrame(data)


def normalize_loads_df(df: pd.DataFrame, *, with_ids: bool) -> pd.DataFrame:
    clean = df.copy().reset_index(drop=True)
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

    expected = LOAD_COLUMNS_EDIT if with_ids else LOAD_COLUMNS
    n = len(clean)
    for col in expected:
        if col not in clean.columns:
            if col in (COL_LOT_ID, COL_LOAD_ID):
                clean[col] = pd.Series([pd.NA] * n, dtype="Int64")
            elif col in (COL_QTY, COL_WEIGHT):
                clean[col] = pd.Series([pd.NA] * n, dtype="Float64")
            else:
                clean[col] = pd.Series([pd.NA] * n, dtype="string")
        elif col in (COL_LOT_ID, COL_LOAD_ID):
            clean[col] = pd.to_numeric(clean[col], errors="coerce").astype("Int64")
        elif col in (COL_QTY, COL_WEIGHT):
            clean[col] = pd.to_numeric(clean[col], errors="coerce").astype("Float64")
        else:
            clean[col] = clean[col].astype("string")
    return clean.loc[:, expected]


def parse_int_id(value) -> int | None:
    if is_blank(value) or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _label_for_load(item, lots: list[LotOptionSchema], labels: list[str]) -> str:
    for lot in lots:
        if lot.id_lote == item.id_lote:
            return lot_label(lot)
    if item.lote_codigo:
        for label in labels:
            if item.lote_codigo in label:
                return label
    return labels[0] if labels else (item.lote_codigo or "")


def loads_editor_df(loads, lots: list[LotOptionSchema], *, with_ids: bool) -> pd.DataFrame:
    if not loads:
        return empty_loads_df(with_ids=with_ids)
    labels = [lot_label(lot) for lot in lots]
    rows = []
    for item in loads:
        row = {
            COL_LOT_ID: item.id_lote,
            COL_LOT: _label_for_load(item, lots, labels),
            COL_QTY: float(item.quantidade) if item.quantidade is not None else pd.NA,
            COL_WEIGHT: float(item.peso_previsto)
            if item.peso_previsto is not None
            else pd.NA,
        }
        if with_ids:
            row = {COL_LOAD_ID: item.id_carga, **row}
        rows.append(row)
    return normalize_loads_df(pd.DataFrame(rows), with_ids=with_ids)


def sync_lot_fields(
    df: pd.DataFrame,
    lots: list[LotOptionSchema],
    previous: pd.DataFrame | None,
    *,
    with_ids: bool,
) -> pd.DataFrame:
    synced = normalize_loads_df(df, with_ids=with_ids)
    by_name = {lot_label(lot): lot for lot in lots}
    by_id = {lot.id_lote: lot for lot in lots}
    prev = (
        normalize_loads_df(previous, with_ids=with_ids)
        if isinstance(previous, pd.DataFrame)
        else None
    )

    for idx in synced.index:
        name_raw = synced.at[idx, COL_LOT]
        name = None if is_blank(name_raw) else str(name_raw).strip()
        lot_id = parse_int_id(synced.at[idx, COL_LOT_ID])

        prev_id = None
        prev_name = None
        if prev is not None and idx in prev.index:
            prev_id = parse_int_id(prev.at[idx, COL_LOT_ID])
            prev_name_raw = prev.at[idx, COL_LOT]
            prev_name = None if is_blank(prev_name_raw) else str(prev_name_raw).strip()

        lot: LotOptionSchema | None = None
        if lot_id is not None and lot_id != prev_id and lot_id in by_id:
            lot = by_id[lot_id]
        elif name and name != prev_name and name in by_name:
            lot = by_name[name]
        elif name and name in by_name:
            lot = by_name[name]
        elif lot_id is not None and lot_id in by_id:
            lot = by_id[lot_id]

        if lot is None:
            continue
        synced.at[idx, COL_LOT_ID] = lot.id_lote
        synced.at[idx, COL_LOT] = lot_label(lot)

    return normalize_loads_df(synced, with_ids=with_ids)


def derived_lot_differ(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    for col in (COL_LOT_ID, COL_LOT):
        if col not in left.columns or col not in right.columns:
            return True
        a = left[col].astype("string").fillna("").tolist()
        b = right[col].astype("string").fillna("").tolist()
        if a != b:
            return True
    return False


def loads_data_editor(
    *,
    state_key: str,
    editor_key: str,
    lots: list[LotOptionSchema],
    initial_loads=None,
    with_ids: bool = False,
) -> pd.DataFrame:
    lot_labels = [lot_label(lot) for lot in lots]
    init_flag = f"_init_{editor_key}"
    prev_key = f"{state_key}_prev"

    if init_flag not in st.session_state:
        st.session_state[state_key] = loads_editor_df(
            initial_loads or [], lots, with_ids=with_ids
        )
        st.session_state[prev_key] = st.session_state[state_key].copy()
        st.session_state[init_flag] = True

    base = normalize_loads_df(st.session_state[state_key], with_ids=with_ids)
    st.session_state[state_key] = base

    column_config = {
        COL_LOT_ID: st.column_config.NumberColumn(
            "ID lote",
            required=False,
            min_value=1,
            step=1,
            format="%d",
            width="small",
        ),
        COL_LOT: st.column_config.SelectboxColumn(
            "Codigo do lote",
            options=lot_labels,
            required=False,
        ),
        COL_QTY: st.column_config.NumberColumn(
            "Quantidade",
            required=False,
            min_value=0.01,
            step=0.01,
            format="%.2f",
        ),
        COL_WEIGHT: st.column_config.NumberColumn(
            "Peso previsto",
            required=False,
            min_value=0.0,
            step=0.01,
            format="%.2f",
        ),
    }
    column_order = list(LOAD_COLUMNS)
    disabled_cols: list[str] = []
    if with_ids:
        column_order = list(LOAD_COLUMNS_EDIT)
        disabled_cols = [COL_LOAD_ID]
        column_config[COL_LOAD_ID] = st.column_config.NumberColumn(
            "ID carga", disabled=True, width="small", format="%d"
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
    edited = normalize_loads_df(edited, with_ids=with_ids)
    previous = st.session_state.get(prev_key)
    synced = sync_lot_fields(
        edited,
        lots,
        previous if isinstance(previous, pd.DataFrame) else None,
        with_ids=with_ids,
    )
    st.session_state[prev_key] = synced.copy()

    if derived_lot_differ(edited, synced):
        st.session_state[state_key] = synced
        st.session_state.pop(editor_key, None)
        st.rerun()

    return synced


def row_has_lot(row) -> bool:
    return not is_blank(row.get(COL_LOT)) or parse_int_id(row.get(COL_LOT_ID)) is not None


def resolve_lot_id(row, lot_map: dict[str, int]) -> int:
    lot_id = parse_int_id(row.get(COL_LOT_ID))
    if lot_id is not None:
        return lot_id
    lot_name = row.get(COL_LOT)
    if not is_blank(lot_name):
        name = str(lot_name).strip()
        if name in lot_map:
            return lot_map[name]
    raise ValueError("Informe o ID ou o lote em cada carga.")


def _optional_float(value) -> float | None:
    if is_blank(value) or value == "":
        return None
    return float(value)


def collect_load_creates(
    rows: pd.DataFrame, lot_map: dict[str, int]
) -> list[LoadCreateSchema]:
    clean = normalize_loads_df(rows.dropna(how="all"), with_ids=False)
    clean = clean[clean.apply(row_has_lot, axis=1)]
    result: list[LoadCreateSchema] = []
    valid_ids = set(lot_map.values())
    for _, row in clean.iterrows():
        lot_id = resolve_lot_id(row, lot_map)
        if lot_id not in valid_ids:
            raise ValueError(f"Lote invalido na grade: ID {lot_id}")
        result.append(
            LoadCreateSchema(
                id_lote=lot_id,
                quantidade=_optional_float(row[COL_QTY]),
                peso_previsto=_optional_float(row[COL_WEIGHT]),
            )
        )
    return result


def persist_load_rows(
    client: LogisticsClient,
    operation_id: int,
    *,
    original_loads,
    rows: pd.DataFrame,
    lot_map: dict[str, int],
) -> None:
    clean = normalize_loads_df(rows.dropna(how="all"), with_ids=True)
    clean = clean[clean.apply(row_has_lot, axis=1)]

    original_by_id = {load.id_carga: load for load in original_loads}
    kept_ids: set[int] = set()
    valid_ids = set(lot_map.values())

    for _, row in clean.iterrows():
        lot_id = resolve_lot_id(row, lot_map)
        if lot_id not in valid_ids:
            raise ValueError(f"Lote invalido na grade: ID {lot_id}")
        qty = _optional_float(row[COL_QTY])
        weight = _optional_float(row[COL_WEIGHT])
        raw_id = row[COL_LOAD_ID] if COL_LOAD_ID in row.index else pd.NA

        if is_blank(raw_id) or raw_id == "":
            client.add_load(
                operation_id,
                LoadCreateSchema(id_lote=lot_id, quantidade=qty, peso_previsto=weight),
            )
            continue

        load_id = int(raw_id)
        original = original_by_id.get(load_id)
        if original is None:
            client.add_load(
                operation_id,
                LoadCreateSchema(id_lote=lot_id, quantidade=qty, peso_previsto=weight),
            )
            continue

        client.update_load(
            operation_id,
            load_id,
            LoadUpdateSchema(id_lote=lot_id, quantidade=qty, peso_previsto=weight),
        )
        kept_ids.add(load_id)

    for load_id in set(original_by_id) - kept_ids:
        client.delete_load(operation_id, load_id)
