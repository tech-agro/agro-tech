"""Dialogs for corrective maintenance."""

from __future__ import annotations

from datetime import date

import streamlit as st

from components.manutencao.constants import STATUS_MANUTENCAO_LABELS, status_label
from components.manutencao.dialog_state import clear_dialog_state, get_dialog
from components.manutencao.lookups import select_maquina
from components.shared.screens import toast_ok
import services.manutencao_client as api

SCOPE = "corretivas"


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


def _find_corretiva(manutencao_id: int) -> dict | None:
    try:
        itens = api.list_manutencoes_corretivas()
    except Exception:
        return None
    for item in itens:
        if int(item["manutencao"]["id_manutencao"]) == int(manutencao_id):
            return item
    return None


def _load_maquinas() -> list[dict]:
    try:
        return api.list_maquinas()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar maquinas: {exc}")
        return []


@st.dialog("Nova manutencao corretiva", width="large")
def _create_dialog(scope: str) -> None:
    maquinas = _load_maquinas()

    id_maquina = select_maquina(
        "Maquina",
        maquinas,
        key=f"_nova_corretiva_maquina_{scope}",
    )
    data_defeito = st.date_input(
        "Data do defeito",
        value=date.today(),
        key=f"_nova_corretiva_data_{scope}",
    )
    defeito_relatado = st.text_area(
        "Defeito relatado",
        key=f"_nova_corretiva_defeito_{scope}",
    )
    causa_raiz = st.text_input(
        "Causa raiz (opcional)",
        key=f"_nova_corretiva_causa_{scope}",
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
    if not defeito_relatado.strip():
        st.error("Informe o defeito relatado.")
        return

    try:
        api.create_manutencao_corretiva(
            {
                "id_maquina": int(id_maquina),
                "status": "ABERTA",
                "dt_inicio": data_defeito.isoformat(),
                "defeito_relatado": defeito_relatado.strip(),
                "causa_raiz": causa_raiz.strip() or None,
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Manutencao corretiva registrada.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes da manutencao corretiva", width="large")
def _view_dialog(scope: str, manutencao_id: int) -> None:
    item = _find_corretiva(manutencao_id)
    if item is None:
        st.error("Manutencao corretiva nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, manutencao_id)
            st.rerun()
        return

    manutencao = item["manutencao"]
    detalhe = item["corretiva"]
    status = manutencao["status"]

    st.text_input("ID", value=str(manutencao_id), disabled=True)
    st.text_input("Maquina", value=item.get("nome_maquina") or "—", disabled=True)
    st.text_input(
        "Status",
        value=status_label(status, STATUS_MANUTENCAO_LABELS),
        disabled=True,
    )
    st.text_input(
        "Data do defeito",
        value=str(manutencao.get("dt_inicio") or "—"),
        disabled=True,
    )
    st.text_area(
        "Defeito relatado",
        value=detalhe.get("defeito_relatado") or "",
        disabled=True,
    )
    st.text_input(
        "Causa raiz",
        value=detalhe.get("causa_raiz") or "—",
        disabled=True,
    )
    st.text_area(
        "Solucao aplicada",
        value=detalhe.get("solucao_aplicada") or "",
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
            key=f"_iniciar_corr_{scope}_{manutencao_id}",
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
            key=f"_custo_corr_{scope}_{manutencao_id}",
        )
        if st.button(
            "Concluir",
            use_container_width=True,
            key=f"_concluir_corr_{scope}_{manutencao_id}",
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
            key=f"_cancelar_corr_{scope}_{manutencao_id}",
        ):
            try:
                api.cancelar_manutencao(manutencao_id)
                toast_ok("Manutencao cancelada.")
                clear_dialog_state(scope, manutencao_id)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if st.button("Fechar", use_container_width=True, key=f"_fechar_corr_{scope}_{manutencao_id}"):
        clear_dialog_state(scope, manutencao_id)
        st.rerun()


@st.dialog("Editar manutencao corretiva", width="large")
def _edit_dialog(scope: str, manutencao_id: int) -> None:
    item = _find_corretiva(manutencao_id)
    if item is None:
        st.error("Manutencao corretiva nao encontrada.")
        if st.button("Fechar"):
            clear_dialog_state(scope, manutencao_id)
            st.rerun()
        return

    manutencao = item["manutencao"]
    detalhe = item["corretiva"]

    dt_inicio_atual = manutencao.get("dt_inicio")
    if isinstance(dt_inicio_atual, str):
        dt_inicio_atual = date.fromisoformat(dt_inicio_atual)

    nova_data = st.date_input(
        "Data do defeito",
        value=dt_inicio_atual or date.today(),
        key=f"_edit_corr_data_{scope}_{manutencao_id}",
    )
    novo_defeito = st.text_area(
        "Defeito relatado",
        value=detalhe.get("defeito_relatado") or "",
        key=f"_edit_corr_defeito_{scope}_{manutencao_id}",
    )
    nova_causa = st.text_input(
        "Causa raiz",
        value=detalhe.get("causa_raiz") or "",
        key=f"_edit_corr_causa_{scope}_{manutencao_id}",
    )
    nova_solucao = st.text_area(
        "Solucao aplicada",
        value=detalhe.get("solucao_aplicada") or "",
        key=f"_edit_corr_solucao_{scope}_{manutencao_id}",
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

    try:
        api.update_manutencao_corretiva(
            manutencao_id,
            {
                "dt_inicio": nova_data.isoformat(),
                "defeito_relatado": novo_defeito.strip() or None,
                "causa_raiz": nova_causa.strip() or None,
                "solucao_aplicada": nova_solucao.strip() or None,
            },
        )
    except Exception as exc:
        st.error(str(exc))
        return

    toast_ok("Detalhes atualizados.")
    clear_dialog_state(scope, manutencao_id)
    st.rerun()


@st.dialog("Cancelar manutencao corretiva")
def _delete_dialog(scope: str, manutencao_id: int) -> None:
    item = _find_corretiva(manutencao_id)
    if item is None:
        st.error("Manutencao corretiva nao encontrada.")
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
        f"Deseja cancelar a manutencao corretiva #{manutencao_id} "
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
