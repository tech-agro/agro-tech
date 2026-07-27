"""Pesticide application data_editor and persistence helpers."""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from app.fitossanidade.schemas.lookups import InputOptionSchema, MachineOptionSchema
from app.fitossanidade.schemas.pesticide_application import (
    PesticideApplicationCreateSchema,
    PesticideApplicationUpdateSchema,
)
from components.fitossanidade.formatters import (
    SELECT_PROMPT,
    input_label,
    is_unset,
    machine_label,
)
from components.shared.formatters import is_blank
from services.fitossanidade_client import PhytosanitaryClient

COL_APP_ID = "id_aplicacao"
COL_INPUT_ID = "id_insumo"
COL_INPUT = "insumo"
COL_MACHINE_ID = "id_maquina"
COL_MACHINE = "maquina"
COL_DOSE = "dose_hectare"
COL_VOLUME = "volume_aplicado"
COL_DT_APP = "dt_aplicacao"
COL_DT_CAR = "dt_carencia"

APP_COLUMNS = [
    COL_INPUT_ID,
    COL_INPUT,
    COL_MACHINE_ID,
    COL_MACHINE,
    COL_DOSE,
    COL_VOLUME,
    COL_DT_APP,
    COL_DT_CAR,
]
APP_COLUMNS_EDIT = [COL_APP_ID, *APP_COLUMNS]


def empty_applications_df(*, with_ids: bool) -> pd.DataFrame:
    data: dict[str, pd.Series] = {
        COL_INPUT_ID: pd.Series(dtype="Int64"),
        COL_INPUT: pd.Series(dtype="string"),
        COL_MACHINE_ID: pd.Series(dtype="Int64"),
        COL_MACHINE: pd.Series(dtype="string"),
        COL_DOSE: pd.Series(dtype="Float64"),
        COL_VOLUME: pd.Series(dtype="Float64"),
        COL_DT_APP: pd.Series(dtype="object"),
        COL_DT_CAR: pd.Series(dtype="object"),
    }
    if with_ids:
        data = {COL_APP_ID: pd.Series(dtype="Int64"), **data}
    return pd.DataFrame(data)


def _to_date(value) -> date | None:
    if is_blank(value) or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()
    except (TypeError, ValueError):
        return None


def normalize_applications_df(df: pd.DataFrame, *, with_ids: bool) -> pd.DataFrame:
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

    expected = APP_COLUMNS_EDIT if with_ids else APP_COLUMNS
    n = len(clean)
    for col in expected:
        if col not in clean.columns:
            if col in (COL_INPUT_ID, COL_APP_ID, COL_MACHINE_ID):
                clean[col] = pd.Series([pd.NA] * n, dtype="Int64")
            elif col in (COL_DOSE, COL_VOLUME):
                clean[col] = pd.Series([pd.NA] * n, dtype="Float64")
            else:
                clean[col] = pd.Series([pd.NA] * n, dtype="object")
        elif col in (COL_INPUT_ID, COL_APP_ID, COL_MACHINE_ID):
            clean[col] = pd.to_numeric(clean[col], errors="coerce").astype("Int64")
        elif col in (COL_DOSE, COL_VOLUME):
            clean[col] = pd.to_numeric(clean[col], errors="coerce").astype("Float64")
        elif col in (COL_DT_APP, COL_DT_CAR):
            clean[col] = clean[col].map(_to_date)
        else:
            clean[col] = clean[col].astype("string")
            if col in (COL_INPUT, COL_MACHINE):
                clean[col] = clean[col].map(
                    lambda v: SELECT_PROMPT if is_unset(v) else str(v)
                )
    return clean.loc[:, expected]


def parse_int_id(value) -> int | None:
    if is_blank(value) or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _label_for_application(
    item, inputs: list[InputOptionSchema], labels: list[str]
) -> str:
    for inp in inputs:
        if inp.id_insumo == item.id_insumo:
            return input_label(inp)
    if item.insumo_nome:
        for label in labels:
            if item.insumo_nome in label:
                return label
    return labels[0] if labels else (item.insumo_nome or "")


def _machine_label_for_application(
    item, machines: list[MachineOptionSchema], labels: list[str]
) -> str:
    if item.id_maquina is None:
        return ""
    for machine in machines:
        if machine.id_maquina == item.id_maquina:
            return machine_label(machine)
    if item.maquina_nome:
        for label in labels:
            if item.maquina_nome in label:
                return label
        return item.maquina_nome
    return labels[0] if labels else f"#{item.id_maquina}"


def applications_editor_df(
    applications,
    inputs: list[InputOptionSchema],
    machines: list[MachineOptionSchema],
    *,
    with_ids: bool,
) -> pd.DataFrame:
    if not applications:
        return empty_applications_df(with_ids=with_ids)

    labels = [input_label(i) for i in inputs]
    machine_labels = [machine_label(m) for m in machines]
    rows = []
    for item in applications:
        row = {
            COL_INPUT_ID: item.id_insumo,
            COL_INPUT: _label_for_application(item, inputs, labels),
            COL_MACHINE_ID: item.id_maquina if item.id_maquina is not None else pd.NA,
            COL_MACHINE: _machine_label_for_application(item, machines, machine_labels)
            if item.id_maquina is not None
            else SELECT_PROMPT,
            COL_DOSE: float(item.dose_hectare) if item.dose_hectare is not None else pd.NA,
            COL_VOLUME: (
                float(item.volume_aplicado)
                if item.volume_aplicado is not None
                else pd.NA
            ),
            COL_DT_APP: item.dt_aplicacao,
            COL_DT_CAR: item.dt_carencia,
        }
        if with_ids:
            row = {COL_APP_ID: item.id_aplicacao, **row}
        rows.append(row)
    return normalize_applications_df(pd.DataFrame(rows), with_ids=with_ids)


def sync_input_fields(
    df: pd.DataFrame,
    inputs: list[InputOptionSchema],
    machines: list[MachineOptionSchema],
    previous: pd.DataFrame | None,
    *,
    with_ids: bool,
) -> pd.DataFrame:
    synced = normalize_applications_df(df, with_ids=with_ids)
    by_name = {input_label(i): i for i in inputs}
    by_id = {i.id_insumo: i for i in inputs}
    machine_by_name = {machine_label(m): m for m in machines}
    machine_by_id = {m.id_maquina: m for m in machines}
    prev = (
        normalize_applications_df(previous, with_ids=with_ids)
        if isinstance(previous, pd.DataFrame)
        else None
    )

    for idx in synced.index:
        name_raw = synced.at[idx, COL_INPUT]
        name = None if is_unset(name_raw) else str(name_raw).strip()
        input_id = parse_int_id(synced.at[idx, COL_INPUT_ID])

        prev_id = None
        prev_name = None
        if prev is not None and idx in prev.index:
            prev_id = parse_int_id(prev.at[idx, COL_INPUT_ID])
            prev_name_raw = prev.at[idx, COL_INPUT]
            prev_name = None if is_unset(prev_name_raw) else str(prev_name_raw).strip()

        inp: InputOptionSchema | None = None
        if input_id is not None and input_id != prev_id and input_id in by_id:
            inp = by_id[input_id]
        elif name and name != prev_name and name in by_name:
            inp = by_name[name]
        elif name and name in by_name:
            inp = by_name[name]
        elif input_id is not None and input_id in by_id:
            inp = by_id[input_id]

        if inp is not None:
            synced.at[idx, COL_INPUT_ID] = inp.id_insumo
            synced.at[idx, COL_INPUT] = input_label(inp)
        else:
            synced.at[idx, COL_INPUT_ID] = pd.NA
            synced.at[idx, COL_INPUT] = SELECT_PROMPT

        machine_name_raw = synced.at[idx, COL_MACHINE]
        machine_name = (
            None if is_unset(machine_name_raw) else str(machine_name_raw).strip()
        )
        machine_id = parse_int_id(synced.at[idx, COL_MACHINE_ID])
        prev_machine_id = None
        prev_machine_name = None
        if prev is not None and idx in prev.index:
            prev_machine_id = parse_int_id(prev.at[idx, COL_MACHINE_ID])
            prev_machine_name_raw = prev.at[idx, COL_MACHINE]
            prev_machine_name = (
                None
                if is_unset(prev_machine_name_raw)
                else str(prev_machine_name_raw).strip()
            )

        machine: MachineOptionSchema | None = None
        if (
            machine_id is not None
            and machine_id != prev_machine_id
            and machine_id in machine_by_id
        ):
            machine = machine_by_id[machine_id]
        elif (
            machine_name
            and machine_name != prev_machine_name
            and machine_name in machine_by_name
        ):
            machine = machine_by_name[machine_name]
        elif machine_name and machine_name in machine_by_name:
            machine = machine_by_name[machine_name]
        elif machine_id is not None and machine_id in machine_by_id:
            machine = machine_by_id[machine_id]

        if machine is not None:
            synced.at[idx, COL_MACHINE_ID] = machine.id_maquina
            synced.at[idx, COL_MACHINE] = machine_label(machine)
        else:
            synced.at[idx, COL_MACHINE_ID] = pd.NA
            synced.at[idx, COL_MACHINE] = SELECT_PROMPT

    return normalize_applications_df(synced, with_ids=with_ids)


def derived_input_differ(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    for col in (COL_INPUT_ID, COL_INPUT, COL_MACHINE_ID, COL_MACHINE):
        if col not in left.columns or col not in right.columns:
            return True
        a = left[col].astype("string").fillna("").tolist()
        b = right[col].astype("string").fillna("").tolist()
        if a != b:
            return True
    return False


def applications_data_editor(
    *,
    state_key: str,
    editor_key: str,
    inputs: list[InputOptionSchema],
    machines: list[MachineOptionSchema] | None = None,
    initial_applications=None,
    with_ids: bool = False,
) -> pd.DataFrame:
    machines = machines or []
    input_labels = [SELECT_PROMPT] + [input_label(i) for i in inputs]
    machine_labels = [SELECT_PROMPT] + [machine_label(m) for m in machines]
    init_flag = f"_init_{editor_key}"
    prev_key = f"{state_key}_prev"

    if init_flag not in st.session_state:
        st.session_state[state_key] = applications_editor_df(
            initial_applications or [], inputs, machines, with_ids=with_ids
        )
        st.session_state[prev_key] = st.session_state[state_key].copy()
        st.session_state[init_flag] = True

    base = normalize_applications_df(st.session_state[state_key], with_ids=with_ids)
    st.session_state[state_key] = base

    column_config = {
        COL_INPUT_ID: st.column_config.NumberColumn(
            "ID insumo",
            required=False,
            min_value=1,
            step=1,
            format="%d",
            width="small",
            help="Apenas defensivos. Informe o ID se souber; o nome preenche sozinho.",
        ),
        COL_INPUT: st.column_config.SelectboxColumn(
            "Insumo (defensivo)",
            options=input_labels,
            required=False,
        ),
        COL_MACHINE_ID: st.column_config.NumberColumn(
            "ID maquina",
            required=False,
            min_value=1,
            step=1,
            format="%d",
            width="small",
        ),
        COL_MACHINE: st.column_config.SelectboxColumn(
            "Maquina",
            options=machine_labels,
            required=False,
            help="Equipamento usado na pulverizacao (opcional).",
        ),
        COL_DOSE: st.column_config.NumberColumn(
            "Dose/ha",
            required=False,
            min_value=0.01,
            step=0.01,
            format="%.2f",
        ),
        COL_VOLUME: st.column_config.NumberColumn(
            "Volume",
            required=False,
            min_value=0.01,
            step=0.01,
            format="%.2f",
            help="Com volume > 0 a API debita o estoque do defensivo.",
        ),
        COL_DT_APP: st.column_config.DateColumn("Aplicacao", required=False),
        COL_DT_CAR: st.column_config.DateColumn(
            "Carencia",
            required=False,
            help="Se vazio, a API calcula com o periodo de carencia do insumo.",
        ),
    }
    column_order = list(APP_COLUMNS)
    disabled_cols: list[str] = []
    if with_ids:
        column_order = list(APP_COLUMNS_EDIT)
        disabled_cols = [COL_APP_ID]
        column_config[COL_APP_ID] = st.column_config.NumberColumn(
            "ID aplicacao", disabled=True, width="small", format="%d"
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
    edited = normalize_applications_df(edited, with_ids=with_ids)

    previous = st.session_state.get(prev_key)
    synced = sync_input_fields(
        edited,
        inputs,
        machines,
        previous if isinstance(previous, pd.DataFrame) else None,
        with_ids=with_ids,
    )
    st.session_state[prev_key] = synced.copy()

    if derived_input_differ(edited, synced):
        st.session_state[state_key] = synced
        st.session_state.pop(editor_key, None)
        st.rerun()

    return synced


def row_has_input(row) -> bool:
    return (
        not is_unset(row.get(COL_INPUT))
        or parse_int_id(row.get(COL_INPUT_ID)) is not None
    )


def resolve_input_id(row, input_map: dict[str, int]) -> int:
    input_id = parse_int_id(row.get(COL_INPUT_ID))
    if input_id is not None:
        return input_id
    input_name = row.get(COL_INPUT)
    if not is_unset(input_name):
        name = str(input_name).strip()
        if name in input_map:
            return input_map[name]
    raise ValueError("Informe o ID ou o nome do insumo em cada aplicacao.")


def resolve_machine_id(row, machine_map: dict[str, int]) -> int | None:
    machine_id = parse_int_id(row.get(COL_MACHINE_ID))
    if machine_id is not None:
        return machine_id
    machine_name = row.get(COL_MACHINE)
    if not is_unset(machine_name):
        name = str(machine_name).strip()
        if name in machine_map:
            return machine_map[name]
    return None


def _optional_float(value) -> float | None:
    if is_blank(value) or value == "":
        return None
    return float(value)


def collect_application_creates(
    rows: pd.DataFrame,
    input_map: dict[str, int],
    machine_map: dict[str, int] | None = None,
) -> list[PesticideApplicationCreateSchema]:
    machine_map = machine_map or {}
    clean = normalize_applications_df(rows.dropna(how="all"), with_ids=False)
    clean = clean[clean.apply(row_has_input, axis=1)]
    result: list[PesticideApplicationCreateSchema] = []
    valid_ids = set(input_map.values())
    valid_machines = set(machine_map.values())
    for _, row in clean.iterrows():
        input_id = resolve_input_id(row, input_map)
        if input_id not in valid_ids:
            raise ValueError(f"Insumo invalido na grade: ID {input_id}")
        machine_id = resolve_machine_id(row, machine_map)
        if machine_id is not None and machine_id not in valid_machines:
            raise ValueError(f"Maquina invalida na grade: ID {machine_id}")
        dt_app = _to_date(row[COL_DT_APP])
        dt_car = _to_date(row[COL_DT_CAR])
        if dt_car is not None and dt_app is not None and dt_car < dt_app:
            raise ValueError(
                "A data de carencia deve ser igual ou posterior a aplicacao."
            )
        result.append(
            PesticideApplicationCreateSchema(
                id_insumo=input_id,
                dose_hectare=_optional_float(row[COL_DOSE]),
                volume_aplicado=_optional_float(row[COL_VOLUME]),
                dt_aplicacao=dt_app,
                dt_carencia=dt_car,
                id_maquina=machine_id,
            )
        )
    return result


def persist_application_rows(
    client: PhytosanitaryClient,
    control_id: int,
    *,
    original_applications,
    rows: pd.DataFrame,
    input_map: dict[str, int],
    machine_map: dict[str, int] | None = None,
) -> None:
    machine_map = machine_map or {}
    clean = normalize_applications_df(rows.dropna(how="all"), with_ids=True)
    clean = clean[clean.apply(row_has_input, axis=1)]

    original_by_id = {a.id_aplicacao: a for a in original_applications}
    kept_ids: set[int] = set()
    valid_ids = set(input_map.values())
    valid_machines = set(machine_map.values())

    for _, row in clean.iterrows():
        input_id = resolve_input_id(row, input_map)
        if input_id not in valid_ids:
            raise ValueError(f"Insumo invalido na grade: ID {input_id}")
        machine_id = resolve_machine_id(row, machine_map)
        if machine_id is not None and machine_id not in valid_machines:
            raise ValueError(f"Maquina invalida na grade: ID {machine_id}")
        dose = _optional_float(row[COL_DOSE])
        volume = _optional_float(row[COL_VOLUME])
        dt_app = _to_date(row[COL_DT_APP])
        dt_car = _to_date(row[COL_DT_CAR])
        if dt_car is not None and dt_app is not None and dt_car < dt_app:
            raise ValueError(
                "A data de carencia deve ser igual ou posterior a aplicacao."
            )
        raw_id = row[COL_APP_ID] if COL_APP_ID in row.index else pd.NA
        create_payload = PesticideApplicationCreateSchema(
            id_insumo=input_id,
            dose_hectare=dose,
            volume_aplicado=volume,
            dt_aplicacao=dt_app,
            dt_carencia=dt_car,
            id_maquina=machine_id,
        )

        if is_blank(raw_id) or raw_id == "":
            client.add_application(control_id, create_payload)
            continue

        application_id = int(raw_id)
        original = original_by_id.get(application_id)
        if original is None:
            client.add_application(control_id, create_payload)
            continue

        client.update_application(
            control_id,
            application_id,
            PesticideApplicationUpdateSchema(
                id_insumo=input_id,
                dose_hectare=dose,
                volume_aplicado=volume,
                dt_aplicacao=dt_app,
                dt_carencia=dt_car,
                id_maquina=machine_id,
            ),
        )
        kept_ids.add(application_id)

    for application_id in set(original_by_id) - kept_ids:
        client.delete_application(control_id, application_id)
