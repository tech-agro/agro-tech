"""Dialogs for maintenance plans (planos de manutencao)."""

from __future__ import annotations

from datetime import date

import streamlit as st

from components.manutencao.constants import PERIODICIDADE_OPCOES, plano_usa_hodometro
from components.manutencao.dialog_state import clear_dialog_state, get_dialog
from components.manutencao.lookups import select_maquina
from components.shared.screens import toast_ok
import services.manutencao_client as api

SCOPE = "planos"


def render(scope: str = SCOPE) -> None:
    dialog = get_dialog(scope)
    if dialog is None:
        return

    kind, entity_id = dialog
    if kind == "create":
        _create_dialog(scope)
    elif entity_id is not None:
        if kind == "view":
            _view_dialog(scope, entity_id)
        elif kind == "edit":
            _edit_dialog(scope, entity_id)
        elif kind == "delete":
            _delete_dialog(scope, entity_id)


def _parse_plan_date(valor) -> date | None:
    if valor is None:
        return None
    if isinstance(valor, str):
        return date.fromisoformat(valor)
    return valor


def _find_plano(plano_id: int) -> dict | None:
    try:
        planos = api.list_planos_manutencao()
    except Exception:
        return None
    for plano in planos:
        if int(plano["id_plano"]) == int(plano_id):
            return plano
    return None


def _load_maquinas() -> list[dict]:
    try:
        return api.list_maquinas()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar maquinas: {exc}")
        return []


@st.dialog("Novo plano de manutencao", width="large")
def _create_dialog(scope: str) -> None:
    maquinas = _load_maquinas()

    id_maquina = select_maquina(
        "Maquina",
        maquinas,
        key=f"_novo_plano_maquina_{scope}",
    )
    periodicidade = st.selectbox(
        "Periodicidade",
        PERIODICIDADE_OPCOES,
        key=f"_novo_plano_periodicidade_{scope}",
    )
    if plano_usa_hodometro({"periodicidade": periodicidade}):
        st.caption(
            "Planos por horas usam hodometro. "
            "A proxima execucao por data nao se aplica."
        )
    else:
        st.caption(
            "A proxima execucao sera calculada automaticamente "
            f"a partir de hoje + {periodicidade}."
        )

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope)
        st.rerun()

    if not salvar:
        return

    if id_maquina is None:
        st.error("Selecione uma maquina.")
        return

    try:
        api.create_plano_manutencao(
            {
                "id_maquina": int(id_maquina),
                "periodicidade": periodicidade,
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Plano cadastrado.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes do plano", width="large")
def _view_dialog(scope: str, plano_id: int) -> None:
    plano = _find_plano(plano_id)
    if plano is None:
        st.error("Plano nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, plano_id)
            st.rerun()
        return

    proxima = _parse_plan_date(plano.get("proxima_execucao"))
    st.text_input("ID", value=str(plano["id_plano"]), disabled=True)
    st.text_input("Maquina", value=plano.get("nome_maquina") or "—", disabled=True)
    st.text_input(
        "Periodicidade",
        value=plano.get("periodicidade") or "—",
        disabled=True,
    )
    if plano_usa_hodometro(plano):
        st.caption("Proxima execucao por data: nao se aplica (controle por hodometro).")
    else:
        st.text_input(
            "Proxima execucao",
            value=proxima.isoformat() if proxima else "—",
            disabled=True,
        )

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, plano_id)
        st.rerun()


@st.dialog("Editar plano de manutencao", width="large")
def _edit_dialog(scope: str, plano_id: int) -> None:
    plano = _find_plano(plano_id)
    if plano is None:
        st.error("Plano nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, plano_id)
            st.rerun()
        return

    st.caption(f"Maquina: {plano.get('nome_maquina') or '—'}")
    proxima = _parse_plan_date(plano.get("proxima_execucao"))
    if plano_usa_hodometro(plano):
        st.caption("Proxima execucao por data: nao se aplica (controle por hodometro).")
    else:
        st.caption(
            "Proxima execucao: "
            f"{proxima.isoformat() if proxima else '—'} "
            "(atualizada automaticamente ao concluir uma preventiva)."
        )

    period_index = (
        PERIODICIDADE_OPCOES.index(plano["periodicidade"])
        if plano.get("periodicidade") in PERIODICIDADE_OPCOES
        else 0
    )
    periodicidade = st.selectbox(
        "Periodicidade",
        PERIODICIDADE_OPCOES,
        index=period_index,
        key=f"_edit_plano_periodicidade_{scope}_{plano_id}",
    )
    if periodicidade != plano.get("periodicidade"):
        st.caption(
            "Ao salvar uma nova periodicidade, a proxima execucao "
            "sera recalculada a partir de hoje."
        )

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, plano_id)
        st.rerun()

    if not salvar:
        return

    try:
        api.update_plano_manutencao(plano_id, {"periodicidade": periodicidade})
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Plano atualizado.")
    clear_dialog_state(scope, plano_id)
    st.rerun()


@st.dialog("Excluir plano de manutencao")
def _delete_dialog(scope: str, plano_id: int) -> None:
    plano = _find_plano(plano_id)
    if plano is None:
        st.error("Plano nao encontrado.")
        if st.button("Fechar"):
            clear_dialog_state(scope, plano_id)
            st.rerun()
        return

    nome = plano.get("nome_maquina") or "maquina"
    st.warning(
        f"Deseja realmente excluir o plano #{plano_id} da maquina **{nome}**?\n\n"
        "Essa acao nao podera ser desfeita."
    )

    col1, col2 = st.columns(2)
    with col1:
        excluir = st.button("Excluir", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, plano_id)
        st.rerun()

    if not excluir:
        return

    try:
        api.delete_plano_manutencao(plano_id)
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Plano excluido.")
    clear_dialog_state(scope, plano_id)
    st.rerun()
