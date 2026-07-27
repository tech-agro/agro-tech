"""Dialogos da entidade agente_nocivo (praga / doenca)."""

from __future__ import annotations

import streamlit as st

from app.fitossanidade.enum import AgentKind
from app.fitossanidade.schemas.harmful_agent import (
    DiseaseCreateSchema,
    HarmfulAgentUpdateSchema,
    PestCreateSchema,
)
from components.fitossanidade.dialog_state import clear_dialog_state, get_dialog
from components.fitossanidade.formatters import kind_label
from components.shared.screens import toast_ok
from services.fitossanidade_client import PhytosanitaryApiError, PhytosanitaryClient

client = PhytosanitaryClient()
SCOPE = "agentes"


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


@st.dialog("Novo agente nocivo")
def _create(scope: str) -> None:
    kind = st.radio("Tipo", ["Praga", "Doenca"], horizontal=True)
    nome_comum = st.text_input("Nome comum")
    nome_cientifico = st.text_input("Nome cientifico")
    if kind == "Praga":
        tipo_praga = st.text_input("Tipo de praga")
        habito = st.text_input("Habito alimentar")
    else:
        causador = st.text_input("Agente causador")
        sintomas = st.text_area("Sintomas")
        condicao = st.text_area("Condicao favoravel")

    c1, c2 = st.columns(2)
    with c1:
        save = st.button("Salvar", type="primary", use_container_width=True)
    with c2:
        cancel = st.button("Cancelar", use_container_width=True)
    if cancel:
        clear_dialog_state(scope)
        st.rerun()
    if not save:
        return
    try:
        if not nome_comum.strip():
            raise ValueError("Informe o nome comum do agente.")
        if kind == "Praga":
            client.create_pest(
                PestCreateSchema(
                    nome_comum=nome_comum.strip(),
                    nome_cientifico=nome_cientifico.strip() or None,
                    tipo_praga=tipo_praga.strip() or None,
                    habito_alimentar=habito.strip() or None,
                )
            )
        else:
            client.create_disease(
                DiseaseCreateSchema(
                    nome_comum=nome_comum.strip(),
                    nome_cientifico=nome_cientifico.strip() or None,
                    agente_causador=causador.strip() or None,
                    sintomas=sintomas.strip() or None,
                    condicao_favoravel=condicao.strip() or None,
                )
            )
        toast_ok("Agente cadastrado.")
        clear_dialog_state(scope)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
    except PhytosanitaryApiError as exc:
        st.error(exc.user_message)


@st.dialog("Detalhes do agente")
def _view(scope: str, agent_id: int) -> None:
    try:
        agent = client.get_agent(agent_id)
    except PhytosanitaryApiError as exc:
        st.error(exc.user_message)
        return

    st.text_input("ID agente", value=str(agent.id_agente), disabled=True)
    st.text_input("Tipo", value=kind_label(agent.kind), disabled=True)
    st.text_input("Nome comum", value=agent.nome_comum or "", disabled=True)
    st.text_input("Nome cientifico", value=agent.nome_cientifico or "", disabled=True)
    if agent.kind == AgentKind.PEST:
        st.text_input("Tipo de praga", value=agent.tipo_praga or "", disabled=True)
        st.text_input(
            "Habito alimentar", value=agent.habito_alimentar or "", disabled=True
        )
    else:
        st.text_input(
            "Agente causador", value=agent.agente_causador or "", disabled=True
        )
        st.text_area("Sintomas", value=agent.sintomas or "", disabled=True)
        st.text_area(
            "Condicao favoravel",
            value=agent.condicao_favoravel or "",
            disabled=True,
        )
    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, agent_id)
        st.rerun()


@st.dialog("Editar agente")
def _edit(scope: str, agent_id: int) -> None:
    try:
        agent = client.get_agent(agent_id)
    except PhytosanitaryApiError as exc:
        st.error(exc.user_message)
        return

    st.caption(f"Tipo: {kind_label(agent.kind)} (nao alteravel)")
    nome_comum = st.text_input("Nome comum", value=agent.nome_comum or "")
    nome_cientifico = st.text_input(
        "Nome cientifico", value=agent.nome_cientifico or ""
    )
    # Pest specialization fields (ignored when agent is a disease)
    if agent.kind == AgentKind.PEST:
        tipo_praga = st.text_input("Tipo de praga", value=agent.tipo_praga or "")
        habito = st.text_input("Habito alimentar", value=agent.habito_alimentar or "")
    else:
        causador = st.text_input(
            "Agente causador", value=agent.agente_causador or ""
        )
        sintomas = st.text_area("Sintomas", value=agent.sintomas or "")
        condicao = st.text_area(
            "Condicao favoravel", value=agent.condicao_favoravel or ""
        )

    c1, c2 = st.columns(2)
    with c1:
        save = st.button("Salvar", type="primary", use_container_width=True)
    with c2:
        cancel = st.button("Cancelar", use_container_width=True)
    if cancel:
        clear_dialog_state(scope, agent_id)
        st.rerun()
    if not save:
        return
    try:
        if not nome_comum.strip():
            raise ValueError("Informe o nome comum do agente.")
        if agent.kind == AgentKind.PEST:
            payload = HarmfulAgentUpdateSchema(
                nome_comum=nome_comum.strip(),
                nome_cientifico=nome_cientifico.strip() or None,
                tipo_praga=tipo_praga.strip() or None,
                habito_alimentar=habito.strip() or None,
            )
        else:
            payload = HarmfulAgentUpdateSchema(
                nome_comum=nome_comum.strip(),
                nome_cientifico=nome_cientifico.strip() or None,
                agente_causador=causador.strip() or None,
                sintomas=sintomas.strip() or None,
                condicao_favoravel=condicao.strip() or None,
            )
        client.update_agent(agent_id, payload)
        toast_ok("Agente atualizado.")
        clear_dialog_state(scope, agent_id)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
    except PhytosanitaryApiError as exc:
        st.error(exc.user_message)


@st.dialog("Excluir agente")
def _delete(scope: str, agent_id: int) -> None:
    st.write(f"Confirma excluir o agente #{agent_id}?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Excluir", type="primary", use_container_width=True):
            try:
                client.delete_agent(agent_id)
                toast_ok("Agente excluido.")
                clear_dialog_state(scope, agent_id)
                st.rerun()
            except PhytosanitaryApiError as exc:
                st.error(exc.user_message)
    with c2:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state(scope, agent_id)
            st.rerun()
