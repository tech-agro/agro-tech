"""Dialogos da entidade controle_fitossanitario.

Fluxo em abas (padrao Logistica):
Controle → Ocorrencias → Aplicacoes

Cada aba salva a propria entidade; severidade do controle e derivada
automaticamente do maior nivel de infestacao das ocorrencias.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from app.fitossanidade.schemas.control import ControlCreateSchema, ControlUpdateSchema
from components.fitossanidade.applications_editor import (
    applications_data_editor,
    collect_application_creates,
    persist_application_rows,
)
from components.fitossanidade.control_tables import (
    applications_view_column_config,
    applications_view_df,
    occurrences_view_column_config,
    occurrences_view_df,
)
from components.fitossanidade.dialog_state import (
    clear_control_editors,
    clear_dialog_state,
    get_dialog,
)
from components.fitossanidade.formatters import (
    agent_label,
    employee_label,
    input_label,
    machine_label,
)
from components.fitossanidade.occurrences_editor import (
    collect_occurrence_creates,
    occurrences_data_editor,
    persist_occurrence_rows,
)
from components.shared.screens import toast_ok
from services.fitossanidade_client import PhytosanitaryApiError, PhytosanitaryClient

client = PhytosanitaryClient()
SCOPE = "controles"


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


@st.dialog("Novo controle", width="large")
def _create(scope: str) -> None:
    try:
        plantings = client.list_plantings()
        employees = client.list_employees()
        agents = client.list_agent_options()
        inputs = client.list_inputs()
        machines = client.list_machines()
    except PhytosanitaryApiError as exc:
        st.error(exc.user_message)
        return

    if not plantings or not employees:
        st.warning(
            "Cadastre ao menos um plantio e um funcionario para criar controles."
        )
        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()
        return

    plantings_by_id = {p.id_plantio: p for p in plantings}
    employees_by_id = {e.id_funcionario: e for e in employees}
    agent_map = {agent_label(a): a.id_agente for a in agents}
    input_map = {input_label(i): i.id_insumo for i in inputs}
    machine_map = {machine_label(m): m.id_maquina for m in machines}

    tab_ctrl, tab_occ, tab_app = st.tabs(["Controle", "Ocorrencias", "Aplicacoes"])

    with tab_ctrl:
        h1, h2 = st.columns(2)
        with h1:
            id_plantio = st.selectbox(
                "ID plantio",
                list(plantings_by_id.keys()),
                format_func=str,
            )
            st.caption(f"Produto: {plantings_by_id[id_plantio].produto_nome or ''}")
        with h2:
            id_funcionario = st.selectbox(
                "ID funcionario",
                list(employees_by_id.keys()),
                format_func=lambda i: employee_label(employees_by_id[i]),
            )
            emp = employees_by_id[id_funcionario]
            if emp.cargo:
                st.caption(f"Cargo: {emp.cargo}")
            if emp.setor:
                st.caption(f"Setor: {emp.setor}")

        dt_identificacao = st.date_input("Data de identificacao", value=date.today())
        st.text_input(
            "Nivel de severidade",
            value="",
            disabled=True,
            help="Calculado automaticamente pelo maior nivel de infestacao das ocorrencias.",
        )
        area = st.number_input(
            "Area afetada (ha)",
            min_value=0.0,
            step=0.01,
            value=0.0,
            format="%.2f",
        )
        recomendacao = st.text_area("Recomendacao")

    with tab_occ:
        if not agents:
            st.info("Cadastre agentes na aba Agentes nocivos da pagina.")
            occ_df = None
        else:
            st.caption("Opcional na criacao. Informe o ID ou o nome do agente.")
            occ_df = occurrences_data_editor(
                state_key="new_control_occurrences",
                editor_key="new_control_occurrences_editor",
                agents=agents,
                with_ids=False,
            )

    with tab_app:
        if not inputs:
            st.info("Nenhum defensivo cadastrado.")
            app_df = None
        else:
            st.caption(
                "Opcional na criacao. Somente insumos da categoria Defensivos."
            )
            app_df = applications_data_editor(
                state_key="new_control_applications",
                editor_key="new_control_applications_editor",
                inputs=inputs,
                machines=machines,
                with_ids=False,
            )

    col_cancel, _, col_save = st.columns([1, 3, 1])
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state(scope)
            st.rerun()
    with col_save:
        if st.button("Criar", type="primary", use_container_width=True):
            try:
                ocorrencias = (
                    collect_occurrence_creates(occ_df, agent_map)
                    if occ_df is not None
                    else []
                )
                applications = (
                    collect_application_creates(app_df, input_map, machine_map)
                    if app_df is not None
                    else []
                )
                control = client.create_control(
                    ControlCreateSchema(
                        id_plantio=id_plantio,
                        id_funcionario=id_funcionario,
                        dt_identificacao=dt_identificacao,
                        nivel_severidade=None,
                        area_afetada_hectares=area if area > 0 else None,
                        recomendacao=recomendacao.strip() or None,
                        ocorrencias=ocorrencias,
                    )
                )
                for payload in applications:
                    client.add_application(control.id_controle, payload)
                clear_dialog_state(scope)
                toast_ok(f"Controle #{control.id_controle} criado.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except PhytosanitaryApiError as exc:
                st.error(exc.user_message)


@st.dialog("Visualizar controle", width="large")
def _view(scope: str, control_id: int) -> None:
    try:
        control = client.get_control(control_id)
        occurrences = client.list_occurrences(control_id)
        applications = client.list_applications(control_id)
    except PhytosanitaryApiError as exc:
        st.error(exc.user_message)
        return

    tab_ctrl, tab_occ, tab_app = st.tabs(["Controle", "Ocorrencias", "Aplicacoes"])

    with tab_ctrl:
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("ID controle", value=str(control.id_controle), disabled=True)
            st.text_input("ID plantio", value=str(control.id_plantio), disabled=True)
            st.text_input(
                "Produto",
                value=control.plantio_produto_nome or "",
                disabled=True,
            )
        with c2:
            st.text_input(
                "ID funcionario", value=str(control.id_funcionario), disabled=True
            )
            st.text_input(
                "Funcionario",
                value=control.funcionario_nome or "",
                disabled=True,
            )
        d1, d2, d3 = st.columns(3)
        with d1:
            st.text_input(
                "Identificacao",
                value=(
                    control.dt_identificacao.isoformat()
                    if control.dt_identificacao
                    else ""
                ),
                disabled=True,
            )
        with d2:
            st.text_input(
                "Severidade",
                value=control.nivel_severidade or "",
                disabled=True,
            )
        with d3:
            st.text_input(
                "Area (ha)",
                value=(
                    f"{float(control.area_afetada_hectares):.2f}"
                    if control.area_afetada_hectares is not None
                    else ""
                ),
                disabled=True,
            )
        st.text_area(
            "Recomendacao",
            value=control.recomendacao or "",
            disabled=True,
        )

    with tab_occ:
        st.dataframe(
            occurrences_view_df(occurrences),
            hide_index=True,
            column_config=occurrences_view_column_config(),
        )

    with tab_app:
        st.dataframe(
            applications_view_df(applications),
            hide_index=True,
            column_config=applications_view_column_config(),
        )

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, control_id)
        st.rerun()


@st.dialog("Editar controle", width="large")
def _edit(scope: str, control_id: int) -> None:
    try:
        control = client.get_control(control_id)
        occurrences = client.list_occurrences(control_id)
        applications = client.list_applications(control_id)
        plantings = client.list_plantings()
        employees = client.list_employees()
        agents = client.list_agent_options()
        inputs = client.list_inputs()
        machines = client.list_machines()
    except PhytosanitaryApiError as exc:
        st.error(exc.user_message)
        return

    if not plantings or not employees:
        st.warning("Plantio e funcionario sao obrigatorios para editar.")
        return

    plantings_by_id = {p.id_plantio: p for p in plantings}
    employees_by_id = {e.id_funcionario: e for e in employees}
    agent_map = {agent_label(a): a.id_agente for a in agents}
    input_map = {input_label(i): i.id_insumo for i in inputs}
    machine_map = {machine_label(m): m.id_maquina for m in machines}

    planting_ids = list(plantings_by_id.keys())
    employee_ids = list(employees_by_id.keys())
    p_idx = (
        planting_ids.index(control.id_plantio)
        if control.id_plantio in planting_ids
        else 0
    )
    e_idx = (
        employee_ids.index(control.id_funcionario)
        if control.id_funcionario in employee_ids
        else 0
    )

    tab_ctrl, tab_occ, tab_app = st.tabs(["Controle", "Ocorrencias", "Aplicacoes"])

    with tab_ctrl:
        st.caption(f"ID controle: {control.id_controle}")
        h1, h2 = st.columns(2)
        with h1:
            id_plantio = st.selectbox(
                "ID plantio",
                planting_ids,
                index=p_idx,
                format_func=str,
            )
            st.caption(f"Produto: {plantings_by_id[id_plantio].produto_nome or ''}")
        with h2:
            id_funcionario = st.selectbox(
                "ID funcionario",
                employee_ids,
                index=e_idx,
                format_func=lambda i: employee_label(employees_by_id[i]),
            )
            emp = employees_by_id[id_funcionario]
            if emp.cargo:
                st.caption(f"Cargo: {emp.cargo}")
            if emp.setor:
                st.caption(f"Setor: {emp.setor}")

        dt_identificacao = st.date_input(
            "Data de identificacao",
            value=control.dt_identificacao or date.today(),
        )
        st.text_input(
            "Nivel de severidade",
            value=control.nivel_severidade or "",
            disabled=True,
            help=(
                "Derivado automaticamente do maior nivel de infestacao "
                "das ocorrencias. Atualiza ao salvar a aba Ocorrencias."
            ),
        )
        area = st.number_input(
            "Area afetada (ha)",
            min_value=0.0,
            step=0.01,
            value=float(control.area_afetada_hectares or 0.0),
            format="%.2f",
        )
        recomendacao = st.text_area(
            "Recomendacao",
            value=control.recomendacao or "",
        )

        if st.button("Salvar controle", type="primary", key=f"save_ctrl_{control_id}"):
            try:
                client.update_control(
                    control_id,
                    ControlUpdateSchema(
                        id_plantio=id_plantio,
                        id_funcionario=id_funcionario,
                        dt_identificacao=dt_identificacao,
                        area_afetada_hectares=area if area > 0 else None,
                        recomendacao=recomendacao.strip() or None,
                    ),
                )
                toast_ok("Controle atualizado.")
                clear_dialog_state(scope, control_id)
                st.rerun()
            except PhytosanitaryApiError as exc:
                st.error(exc.user_message)

    with tab_occ:
        st.caption(
            "Adicione, edite ou remova ocorrencias. "
            "Ao salvar, a severidade do controle e recalculada."
        )
        if not agents:
            st.info("Cadastre agentes na aba Agentes nocivos da pagina.")
            st.dataframe(
                occurrences_view_df(occurrences),
                hide_index=True,
                column_config=occurrences_view_column_config(),
            )
        else:
            occ_df = occurrences_data_editor(
                state_key=f"edit_control_occurrences_{control_id}",
                editor_key=f"edit_control_occurrences_editor_{control_id}",
                agents=agents,
                initial_occurrences=occurrences,
                with_ids=True,
            )
            if st.button(
                "Salvar ocorrencias",
                type="primary",
                key=f"save_occ_{control_id}",
            ):
                try:
                    persist_occurrence_rows(
                        client,
                        control_id,
                        original_occurrences=occurrences,
                        rows=occ_df,
                        agent_map=agent_map,
                    )
                    clear_control_editors(control_id)
                    toast_ok("Ocorrencias atualizadas. Severidade recalculada.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
                except PhytosanitaryApiError as exc:
                    st.error(exc.user_message)

    with tab_app:
        st.caption(
            "Adicione, edite ou remova aplicacoes de defensivo. "
            "Volume > 0 debita estoque."
        )
        if not inputs:
            st.info("Nenhum defensivo cadastrado.")
            st.dataframe(
                applications_view_df(applications),
                hide_index=True,
                column_config=applications_view_column_config(),
            )
        else:
            app_df = applications_data_editor(
                state_key=f"edit_control_applications_{control_id}",
                editor_key=f"edit_control_applications_editor_{control_id}",
                inputs=inputs,
                machines=machines,
                initial_applications=applications,
                with_ids=True,
            )
            if st.button(
                "Salvar aplicacoes",
                type="primary",
                key=f"save_app_{control_id}",
            ):
                try:
                    persist_application_rows(
                        client,
                        control_id,
                        original_applications=applications,
                        rows=app_df,
                        input_map=input_map,
                        machine_map=machine_map,
                    )
                    clear_control_editors(control_id)
                    toast_ok("Aplicacoes atualizadas.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
                except PhytosanitaryApiError as exc:
                    st.error(exc.user_message)

    if st.button("Fechar", use_container_width=True, key=f"close_edit_{control_id}"):
        clear_dialog_state(scope, control_id)
        st.rerun()


@st.dialog("Excluir controle")
def _delete(scope: str, control_id: int) -> None:
    st.write(
        f"Confirma excluir o controle #{control_id}? "
        "Ocorrencias e aplicacoes vinculadas tambem serao removidas."
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Excluir", type="primary", use_container_width=True):
            try:
                client.delete_control(control_id)
                clear_dialog_state(scope, control_id)
                toast_ok("Controle excluido.")
                st.rerun()
            except PhytosanitaryApiError as exc:
                st.error(exc.user_message)
    with c2:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state(scope, control_id)
            st.rerun()
