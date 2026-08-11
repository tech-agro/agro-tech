"""Dialogs for preventive maintenance."""

from __future__ import annotations

from datetime import date

import streamlit as st

from components.manutencao.constants import (
    STATUS_MANUTENCAO_LABELS,
    plano_usa_hodometro,
    status_label,
)
from components.manutencao.dialog_state import clear_dialog_state, get_dialog
from components.manutencao.lookups import select_plano
from components.shared.screens import toast_ok
import services.manutencao_client as api

SCOPE = "preventivas"


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


def suggested_preventive_date(plano: dict | None) -> date:
    if plano is not None and not plano_usa_hodometro(plano):
        proxima = _parse_plan_date(plano.get("proxima_execucao"))
        if proxima is not None:
            return proxima
    return date.today()


def _find_preventiva(manutencao_id: int) -> dict | None:
    try:
        itens = api.list_manutencoes_preventivas()
    except Exception:
        return None
    for item in itens:
        if int(item["manutencao"]["id_manutencao"]) == int(manutencao_id):
            return item
    return None


def _load_planos() -> list[dict]:
    try:
        return api.list_planos_manutencao()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar planos: {exc}")
        return []


@st.dialog("Nova manutencao preventiva", width="large")
def _create_dialog(scope: str) -> None:
    planos = _load_planos()
    plano = select_plano(
        "Plano",
        planos,
        key=f"_nova_preventiva_plano_{scope}",
    )

    if plano:
        if plano_usa_hodometro(plano):
            st.caption("Este plano e controlado por hodometro.")
        else:
            proxima = _parse_plan_date(plano.get("proxima_execucao"))
            if proxima is not None:
                st.caption(f"Proxima execucao prevista do plano: {proxima.isoformat()}")

    data_execucao = st.date_input(
        "Data de execucao",
        value=suggested_preventive_date(plano),
        key=f"_nova_preventiva_data_{scope}",
    )

    hodometro_execucao = None
    if plano and plano_usa_hodometro(plano):
        hodometro_execucao = st.number_input(
            "Hodometro atual",
            min_value=0.0,
            step=0.1,
            format="%.1f",
            key=f"_nova_preventiva_hodometro_{scope}",
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

    if plano is None:
        st.error("Selecione um plano.")
        return

    payload: dict = {
        "id_maquina": int(plano["id_maquina"]),
        "id_plano": int(plano["id_plano"]),
        "status": "ABERTA",
        "dt_inicio": data_execucao.isoformat(),
    }
    if hodometro_execucao is not None and hodometro_execucao > 0:
        payload["hodometro_execucao"] = float(hodometro_execucao)

    try:
        api.create_manutencao_preventiva(payload)
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Manutencao preventiva registrada.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes da manutencao preventiva", width="large")
def _view_dialog(scope: str, manutencao_id: int) -> None:
    item = _find_preventiva(manutencao_id)
    if item is None:
        st.error("Manutencao preventiva nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, manutencao_id)
            st.rerun()
        return

    manutencao = item["manutencao"]
    detalhe = item["preventiva"]
    status = manutencao["status"]

    st.text_input("ID", value=str(manutencao_id), disabled=True)
    st.text_input("Maquina", value=item.get("nome_maquina") or "—", disabled=True)
    st.text_input(
        "Status",
        value=status_label(status, STATUS_MANUTENCAO_LABELS),
        disabled=True,
    )
    st.text_input(
        "Plano",
        value=str(detalhe.get("id_plano") or "—"),
        disabled=True,
    )
    st.text_input(
        "Periodicidade",
        value=item.get("periodicidade") or "—",
        disabled=True,
    )
    st.text_input(
        "Data de execucao",
        value=str(manutencao.get("dt_inicio") or "—"),
        disabled=True,
    )
    st.text_input(
        "Hodometro",
        value=str(detalhe.get("hodometro_execucao") or "—"),
        disabled=True,
    )
    st.text_input(
        "Proxima execucao do plano",
        value=str(item.get("proxima_execucao_plano") or "—"),
        disabled=True,
    )
    st.text_input(
        "Custo",
        value=str(manutencao.get("custo") or "—"),
        disabled=True,
    )

    st.divider()
    st.caption("Fluxo da manutencao")

    if status == "ABERTA":
        if st.button(
            "Iniciar",
            use_container_width=True,
            key=f"_iniciar_prev_{scope}_{manutencao_id}",
        ):
            try:
                api.iniciar_manutencao(manutencao_id)
                toast_ok("Manutencao iniciada.")
                clear_dialog_state(scope, manutencao_id)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if status in {"ABERTA", "EM_EXECUCAO"}:
        custo = st.number_input(
            "Custo",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            key=f"_custo_prev_{scope}_{manutencao_id}",
        )
        if st.button(
            "Concluir",
            use_container_width=True,
            key=f"_concluir_prev_{scope}_{manutencao_id}",
        ):
            if custo <= 0:
                st.error("Informe o custo da manutencao.")
            else:
                try:
                    api.concluir_manutencao(manutencao_id, {"custo": float(custo)})
                    toast_ok("Manutencao concluida.")
                    clear_dialog_state(scope, manutencao_id)
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    if status not in {"CONCLUIDA", "CANCELADA"}:
        if st.button(
            "Cancelar",
            use_container_width=True,
            key=f"_cancelar_prev_{scope}_{manutencao_id}",
        ):
            try:
                api.cancelar_manutencao(manutencao_id)
                toast_ok("Manutencao cancelada.")
                clear_dialog_state(scope, manutencao_id)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if st.button("Fechar", use_container_width=True, key=f"_fechar_prev_{scope}_{manutencao_id}"):
        clear_dialog_state(scope, manutencao_id)
        st.rerun()


@st.dialog("Editar manutencao preventiva", width="large")
def _edit_dialog(scope: str, manutencao_id: int) -> None:
    item = _find_preventiva(manutencao_id)
    if item is None:
        st.error("Manutencao preventiva nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, manutencao_id)
            st.rerun()
        return

    manutencao = item["manutencao"]
    detalhe = item["preventiva"]

    dt_inicio_atual = manutencao.get("dt_inicio")
    if isinstance(dt_inicio_atual, str):
        dt_inicio_atual = date.fromisoformat(dt_inicio_atual)

    nova_data = st.date_input(
        "Data de execucao",
        value=dt_inicio_atual or date.today(),
        key=f"_edit_prev_data_{scope}_{manutencao_id}",
    )
    novo_hodometro = st.number_input(
        "Hodometro de execucao",
        min_value=0.0,
        step=0.1,
        format="%.1f",
        value=float(detalhe.get("hodometro_execucao") or 0.0),
        key=f"_edit_prev_hodometro_{scope}_{manutencao_id}",
    )

    col1, col2 = st.columns(2)
    with col1:
        salvar = st.button("Salvar", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope, manutencao_id)
        st.rerun()

    if not salvar:
        return

    payload: dict = {"dt_inicio": nova_data.isoformat()}
    if novo_hodometro > 0:
        payload["hodometro_execucao"] = float(novo_hodometro)

    try:
        api.update_manutencao_preventiva(manutencao_id, payload)
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Detalhes atualizados.")
    clear_dialog_state(scope, manutencao_id)
    st.rerun()


@st.dialog("Cancelar manutencao preventiva")
def _delete_dialog(scope: str, manutencao_id: int) -> None:
    item = _find_preventiva(manutencao_id)
    if item is None:
        st.error("Manutencao preventiva nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, manutencao_id)
            st.rerun()
        return

    nome = item.get("nome_maquina") or "maquina"
    status = item["manutencao"]["status"]
    if status in {"CONCLUIDA", "CANCELADA"}:
        st.error("Esta manutencao nao pode ser cancelada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, manutencao_id)
            st.rerun()
        return

    st.warning(
        f"Deseja cancelar a manutencao preventiva #{manutencao_id} "
        f"da maquina **{nome}**?"
    )

    col1, col2 = st.columns(2)
    with col1:
        confirmar = st.button("Cancelar manutencao", use_container_width=True)
    with col2:
        voltar = st.button("Voltar", use_container_width=True)

    if voltar:
        clear_dialog_state(scope, manutencao_id)
        st.rerun()

    if not confirmar:
        return

    try:
        api.cancelar_manutencao(manutencao_id)
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Manutencao cancelada.")
    clear_dialog_state(scope, manutencao_id)
    st.rerun()
