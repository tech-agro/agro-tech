"""Dialogo de consulta da entidade carga (somente leitura)."""

from __future__ import annotations

import streamlit as st

from components.logistica.dialog_state import clear_dialog_state, get_dialog
from components.logistica.formatters import DISPATCH_STATUS_LABELS
from components.logistica.operation_tables import weighings_view_df
from services.logistica_client import LogisticsApiError, LogisticsClient

client = LogisticsClient()


def render(scope: str) -> None:
    dialog = get_dialog(scope)
    if dialog is None:
        return
    kind, entity_id = dialog
    if entity_id is not None and kind == "view":
        _view(scope, entity_id)


@st.dialog("Detalhes da carga", width="large")
def _view(scope: str, load_id: int) -> None:
    try:
        load = client.get_load(load_id)
        weighings = client.list_weighings(load.id_operacao, load_id)
        dispatch = client.get_dispatch(load.id_operacao, load_id)
    except LogisticsApiError as exc:
        st.error(exc.user_message)
        return

    st.text_input("ID carga", value=str(load.id_carga), disabled=True)
    st.text_input("ID operacao", value=str(load.id_operacao), disabled=True)
    st.text_input("ID lote", value=str(load.id_lote), disabled=True)
    st.text_input("Codigo lote", value=load.lote_codigo or "", disabled=True)
    st.text_input("Produto", value=load.produto_nome or "", disabled=True)
    st.text_input(
        "Quantidade",
        value="" if load.quantidade is None else str(load.quantidade),
        disabled=True,
    )
    st.text_input(
        "Peso previsto",
        value="" if load.peso_previsto is None else str(load.peso_previsto),
        disabled=True,
    )

    st.markdown("##### Pesagens")
    st.dataframe(weighings_view_df(weighings), use_container_width=True, hide_index=True)

    st.markdown("##### Expedicao")
    if dispatch is None:
        st.info("Expedicao ainda nao iniciada.")
    else:
        st.text_input(
            "Status",
            value=DISPATCH_STATUS_LABELS.get(dispatch.status, dispatch.status.value),
            disabled=True,
        )
        st.text_input(
            "Data saida",
            value=(
                dispatch.data_saida.isoformat(sep=" ", timespec="minutes")
                if dispatch.data_saida
                else ""
            ),
            disabled=True,
        )
        st.text_input(
            "Data chegada prevista",
            value=(
                dispatch.data_chegada_prevista.isoformat(sep=" ", timespec="minutes")
                if dispatch.data_chegada_prevista
                else ""
            ),
            disabled=True,
        )
        st.text_input(
            "Data entrega",
            value=(
                dispatch.data_entrega.isoformat(sep=" ", timespec="minutes")
                if dispatch.data_entrega
                else ""
            ),
            disabled=True,
        )
        st.text_input(
            "ID motorista",
            value=(
                "" if dispatch.id_funcionario is None else str(dispatch.id_funcionario)
            ),
            disabled=True,
        )
        st.text_input("Motorista", value=dispatch.motorista_nome or "", disabled=True)
        st.text_area("Observacoes", value=dispatch.observacoes or "", disabled=True)

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, load_id)
        st.rerun()
