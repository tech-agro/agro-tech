"""Occurrence data_editor and persistence helpers for phytosanitary controls."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.fitossanidade.schemas.agent_occurrence import (
    AgentOccurrenceCreateSchema,
    AgentOccurrenceUpdateSchema,
)
from app.fitossanidade.schemas.lookups import AgentOptionSchema
from components.fitossanidade.formatters import (
    SELECT_PROMPT,
    agent_label,
    INFESTATION_OPTIONS,
    is_unset,
)
from components.shared.formatters import is_blank
from services.fitossanidade_client import PhytosanitaryClient

COL_OCC_ID = "id_ocorrencia"
COL_AGENT_ID = "id_agente"
COL_AGENT = "agente"
COL_INFESTATION = "nivel_infestacao"
COL_METHOD = "metodo_controle"

OCC_COLUMNS = [COL_AGENT_ID, COL_AGENT, COL_INFESTATION, COL_METHOD]
OCC_COLUMNS_EDIT = [COL_OCC_ID, *OCC_COLUMNS]


def empty_occurrences_df(*, with_ids: bool) -> pd.DataFrame:
    data: dict[str, pd.Series] = {
        COL_AGENT_ID: pd.Series(dtype="Int64"),
        COL_AGENT: pd.Series(dtype="string"),
        COL_INFESTATION: pd.Series(dtype="string"),
        COL_METHOD: pd.Series(dtype="string"),
    }
    if with_ids:
        data = {COL_OCC_ID: pd.Series(dtype="Int64"), **data}
    return pd.DataFrame(data)


def normalize_occurrences_df(df: pd.DataFrame, *, with_ids: bool) -> pd.DataFrame:
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

    expected = OCC_COLUMNS_EDIT if with_ids else OCC_COLUMNS
    n = len(clean)
    for col in expected:
        if col not in clean.columns:
            if col in (COL_AGENT_ID, COL_OCC_ID):
                clean[col] = pd.Series([pd.NA] * n, dtype="Int64")
            else:
                clean[col] = pd.Series([pd.NA] * n, dtype="string")
        elif col in (COL_AGENT_ID, COL_OCC_ID):
            clean[col] = pd.to_numeric(clean[col], errors="coerce").astype("Int64")
        else:
            clean[col] = clean[col].astype("string")
            if col in (COL_AGENT, COL_INFESTATION):
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


def _label_for_occurrence(item, agents: list[AgentOptionSchema], labels: list[str]) -> str:
    for agent in agents:
        if agent.id_agente == item.id_agente:
            return agent_label(agent)
    if item.agente_nome:
        for label in labels:
            if item.agente_nome in label:
                return label
    return labels[0] if labels else (item.agente_nome or "")


def occurrences_editor_df(
    occurrences,
    agents: list[AgentOptionSchema],
    *,
    with_ids: bool,
) -> pd.DataFrame:
    if not occurrences:
        return empty_occurrences_df(with_ids=with_ids)

    labels = [agent_label(a) for a in agents]
    rows = []
    for item in occurrences:
        row = {
            COL_AGENT_ID: item.id_agente,
            COL_AGENT: _label_for_occurrence(item, agents, labels),
            COL_INFESTATION: item.nivel_infestacao or SELECT_PROMPT,
            COL_METHOD: item.metodo_controle or "",
        }
        if with_ids:
            row = {COL_OCC_ID: item.id_ocorrencia, **row}
        rows.append(row)
    return normalize_occurrences_df(pd.DataFrame(rows), with_ids=with_ids)


def sync_agent_fields(
    df: pd.DataFrame,
    agents: list[AgentOptionSchema],
    previous: pd.DataFrame | None,
    *,
    with_ids: bool,
) -> pd.DataFrame:
    synced = normalize_occurrences_df(df, with_ids=with_ids)
    by_name = {agent_label(a): a for a in agents}
    by_id = {a.id_agente: a for a in agents}
    prev = (
        normalize_occurrences_df(previous, with_ids=with_ids)
        if isinstance(previous, pd.DataFrame)
        else None
    )

    for idx in synced.index:
        name_raw = synced.at[idx, COL_AGENT]
        name = None if is_unset(name_raw) else str(name_raw).strip()
        agent_id = parse_int_id(synced.at[idx, COL_AGENT_ID])

        prev_id = None
        prev_name = None
        if prev is not None and idx in prev.index:
            prev_id = parse_int_id(prev.at[idx, COL_AGENT_ID])
            prev_name_raw = prev.at[idx, COL_AGENT]
            prev_name = None if is_unset(prev_name_raw) else str(prev_name_raw).strip()

        agent: AgentOptionSchema | None = None
        if agent_id is not None and agent_id != prev_id and agent_id in by_id:
            agent = by_id[agent_id]
        elif name and name != prev_name and name in by_name:
            agent = by_name[name]
        elif name and name in by_name:
            agent = by_name[name]
        elif agent_id is not None and agent_id in by_id:
            agent = by_id[agent_id]

        if agent is None:
            synced.at[idx, COL_AGENT_ID] = pd.NA
            synced.at[idx, COL_AGENT] = SELECT_PROMPT
            continue

        synced.at[idx, COL_AGENT_ID] = agent.id_agente
        synced.at[idx, COL_AGENT] = agent_label(agent)

    return normalize_occurrences_df(synced, with_ids=with_ids)


def derived_agent_differ(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    for col in (COL_AGENT_ID, COL_AGENT):
        if col not in left.columns or col not in right.columns:
            return True
        a = left[col].astype("string").fillna("").tolist()
        b = right[col].astype("string").fillna("").tolist()
        if a != b:
            return True
    return False


def occurrences_data_editor(
    *,
    state_key: str,
    editor_key: str,
    agents: list[AgentOptionSchema],
    initial_occurrences=None,
    with_ids: bool = False,
) -> pd.DataFrame:
    agent_labels = [SELECT_PROMPT] + [agent_label(a) for a in agents]
    init_flag = f"_init_{editor_key}"
    prev_key = f"{state_key}_prev"

    if init_flag not in st.session_state:
        st.session_state[state_key] = occurrences_editor_df(
            initial_occurrences or [], agents, with_ids=with_ids
        )
        st.session_state[prev_key] = st.session_state[state_key].copy()
        st.session_state[init_flag] = True

    base = normalize_occurrences_df(st.session_state[state_key], with_ids=with_ids)
    st.session_state[state_key] = base

    column_config = {
        COL_AGENT_ID: st.column_config.NumberColumn(
            "ID agente",
            required=False,
            min_value=1,
            step=1,
            format="%d",
            width="small",
            help="Informe o ID do agente se souber; o nome preenche sozinho.",
        ),
        COL_AGENT: st.column_config.SelectboxColumn(
            "Agente",
            options=agent_labels,
            required=False,
        ),
        COL_INFESTATION: st.column_config.SelectboxColumn(
            "Nivel de infestacao",
            options=INFESTATION_OPTIONS,
            required=False,
            help="Define a severidade do controle (pior nivel entre as ocorrencias).",
        ),
        COL_METHOD: st.column_config.TextColumn("Metodo de controle"),
    }
    column_order = list(OCC_COLUMNS)
    disabled_cols: list[str] = []
    if with_ids:
        column_order = list(OCC_COLUMNS_EDIT)
        disabled_cols = [COL_OCC_ID]
        column_config[COL_OCC_ID] = st.column_config.NumberColumn(
            "ID ocorrencia", disabled=True, width="small", format="%d"
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
    edited = normalize_occurrences_df(edited, with_ids=with_ids)

    previous = st.session_state.get(prev_key)
    synced = sync_agent_fields(
        edited,
        agents,
        previous if isinstance(previous, pd.DataFrame) else None,
        with_ids=with_ids,
    )
    st.session_state[prev_key] = synced.copy()

    if derived_agent_differ(edited, synced):
        st.session_state[state_key] = synced
        st.session_state.pop(editor_key, None)
        st.rerun()

    return synced


def row_has_agent(row) -> bool:
    return (
        not is_unset(row.get(COL_AGENT))
        or parse_int_id(row.get(COL_AGENT_ID)) is not None
    )


def resolve_agent_id(row, agent_map: dict[str, int]) -> int:
    agent_id = parse_int_id(row.get(COL_AGENT_ID))
    if agent_id is not None:
        return agent_id
    agent_name = row.get(COL_AGENT)
    if not is_unset(agent_name):
        name = str(agent_name).strip()
        if name in agent_map:
            return agent_map[name]
    raise ValueError("Informe o ID ou o nome do agente em cada ocorrencia.")


def collect_occurrence_creates(
    rows: pd.DataFrame, agent_map: dict[str, int]
) -> list[AgentOccurrenceCreateSchema]:
    clean = normalize_occurrences_df(rows.dropna(how="all"), with_ids=False)
    clean = clean[clean.apply(row_has_agent, axis=1)]
    result = []
    valid_ids = set(agent_map.values())
    for _, row in clean.iterrows():
        agent_id = resolve_agent_id(row, agent_map)
        if agent_id not in valid_ids:
            raise ValueError(f"Agente invalido na grade: ID {agent_id}")
        infestation = row[COL_INFESTATION]
        method = row[COL_METHOD]
        result.append(
            AgentOccurrenceCreateSchema(
                id_agente=agent_id,
                nivel_infestacao=None if is_unset(infestation) else str(infestation),
                metodo_controle=(
                    None
                    if is_blank(method) or str(method).strip() == ""
                    else str(method)
                ),
            )
        )
    return result


def persist_occurrence_rows(
    client: PhytosanitaryClient,
    control_id: int,
    *,
    original_occurrences,
    rows: pd.DataFrame,
    agent_map: dict[str, int],
) -> None:
    clean = normalize_occurrences_df(rows.dropna(how="all"), with_ids=True)
    clean = clean[clean.apply(row_has_agent, axis=1)]

    original_by_id = {o.id_ocorrencia: o for o in original_occurrences}
    kept_ids: set[int] = set()
    valid_ids = set(agent_map.values())

    for _, row in clean.iterrows():
        agent_id = resolve_agent_id(row, agent_map)
        if agent_id not in valid_ids:
            raise ValueError(f"Agente invalido na grade: ID {agent_id}")
        infestation = row[COL_INFESTATION]
        method = row[COL_METHOD]
        nivel = None if is_unset(infestation) else str(infestation)
        metodo = (
            None if is_blank(method) or str(method).strip() == "" else str(method)
        )
        raw_id = row[COL_OCC_ID] if COL_OCC_ID in row.index else pd.NA

        if is_blank(raw_id) or raw_id == "":
            client.add_occurrence(
                control_id,
                AgentOccurrenceCreateSchema(
                    id_agente=agent_id,
                    nivel_infestacao=nivel,
                    metodo_controle=metodo,
                ),
            )
            continue

        occurrence_id = int(raw_id)
        original = original_by_id.get(occurrence_id)
        if original is None:
            client.add_occurrence(
                control_id,
                AgentOccurrenceCreateSchema(
                    id_agente=agent_id,
                    nivel_infestacao=nivel,
                    metodo_controle=metodo,
                ),
            )
            continue

        client.update_occurrence(
            control_id,
            occurrence_id,
            AgentOccurrenceUpdateSchema(
                id_agente=agent_id,
                nivel_infestacao=nivel,
                metodo_controle=metodo,
            ),
        )
        kept_ids.add(occurrence_id)

    for occurrence_id in set(original_by_id) - kept_ids:
        client.delete_occurrence(control_id, occurrence_id)
