"""Diálogos da entidade Venda."""

from __future__ import annotations

from datetime import date

import streamlit as st

from app.comercial.models import ItemVendaEntrada, NovaVenda
from components.comercial.dialog_state import clear_dialog_state, get_dialog
from components.comercial.formatters import centro_custo_label, cliente_label, lote_label, produto_label
from components.comercial.vendas_tables import STATUS_RECEBIMENTO, itens_venda_df
from services.comercial_client import ComercialApiError, ComercialClient
from services.estoque_client import EstoqueApiError, EstoqueClient
from services.financeiro_client import FinanceiroApiError, FinanceiroClient

client = ComercialClient()
estoque_client = EstoqueClient()
financeiro_client = FinanceiroClient()

_ITENS_KEY = "nova_venda_itens"


def render(scope: str) -> None:
    """Renderiza o diálogo atualmente aberto."""
    dialog = get_dialog(scope)

    if dialog is None:
        return

    kind, entity_id = dialog

    if kind == "create":
        _create_dialog(scope)
    elif kind == "view" and entity_id is not None:
        _view_dialog(scope, entity_id)


@st.dialog("Nova venda", width="large")
def _create_dialog(scope: str) -> None:
    try:
        clientes = client.list_cliente_options()
        centros_custo = client.list_centro_custo_options()
        produtos = client.list_produto_options()
        lotes = client.list_lote_options()
        estoques = estoque_client.list_estoque_options()
    except (ComercialApiError, EstoqueApiError) as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()
        return

    if not clientes or not centros_custo or not produtos or not estoques:
        st.info(
            "Cadastre ao menos um cliente ativo, um centro de custo, um produto e um "
            "estoque antes de registrar uma venda."
        )
        if st.button("Fechar"):
            clear_dialog_state(scope)
            st.rerun()
        return

    st.session_state.setdefault(_ITENS_KEY, [])

    cliente = st.selectbox("Cliente", options=clientes, format_func=cliente_label)
    centro_custo = st.selectbox("Centro de custo", options=centros_custo, format_func=centro_custo_label)
    data_venda = st.date_input("Data da venda", value=date.today())

    st.divider()
    st.caption(
        "Cada item precisa de um lote liberado (rastreabilidade obrigatória para faturar) "
        "e saldo suficiente no estoque informado."
    )

    with st.form("form_novo_item_venda", clear_on_submit=True):
        produto = st.selectbox("Produto", options=produtos, format_func=produto_label)
        estoque = st.selectbox("Estoque de origem", options=estoques, format_func=lambda e: f"{e.descricao} (#{e.id_estoque})")
        lote = st.selectbox("Lote", options=lotes, format_func=lote_label) if lotes else None
        quantidade = st.number_input("Quantidade", min_value=0.01, step=0.01)
        valor_unitario = st.number_input("Valor unitário", min_value=0.0, step=0.01)
        adicionar = st.form_submit_button("Adicionar item")

    if adicionar:
        if lote is None:
            st.error("Cadastre um lote no módulo Estoque antes de adicionar itens à venda.")
        else:
            st.session_state[_ITENS_KEY].append(
                {
                    "produto_label": produto_label(produto),
                    "id_produto": produto.id_produto,
                    "id_estoque": estoque.id_estoque,
                    "lote_label": lote_label(lote),
                    "id_lote": lote.id_lote,
                    "quantidade": float(quantidade),
                    "valor_unitario": float(valor_unitario),
                }
            )
            st.rerun()

    itens = st.session_state[_ITENS_KEY]
    if itens:
        st.dataframe(
            [
                {
                    "Produto": item["produto_label"],
                    "Lote": item["lote_label"],
                    "Quantidade": item["quantidade"],
                    "Valor unitário": item["valor_unitario"],
                }
                for item in itens
            ],
            use_container_width=True,
            hide_index=True,
        )
        total = sum(item["quantidade"] * item["valor_unitario"] for item in itens)
        st.caption(f"Total: R$ {total:.2f}")

        if st.button("Remover último item"):
            itens.pop()
            st.rerun()
    else:
        st.info("Nenhum item adicionado ainda.")

    col1, col2 = st.columns(2)
    with col1:
        registrar = st.button("Registrar venda", type="primary", use_container_width=True)
    with col2:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        clear_dialog_state(scope)
        st.rerun()

    if not registrar:
        return

    if not itens:
        st.error("Adicione ao menos um item antes de registrar a venda.")
        return

    payload = NovaVenda(
        id_cliente=cliente.id_cliente,
        id_centro_custo=centro_custo.id_centro_custo,
        data_venda=data_venda,
        itens=[
            ItemVendaEntrada(
                id_produto=item["id_produto"],
                id_estoque=item["id_estoque"],
                id_lote=item["id_lote"],
                quantidade=item["quantidade"],
                valor_unitario=item["valor_unitario"],
            )
            for item in itens
        ],
    )

    try:
        client.registrar_venda(payload)
    except ComercialApiError as exc:
        st.error(exc.user_message)
        return

    st.toast("Venda registrada com sucesso.")
    clear_dialog_state(scope)
    st.rerun()


@st.dialog("Detalhes da venda", width="large")
def _view_dialog(scope: str, id_venda: int) -> None:
    try:
        venda = client.get_venda(id_venda)
    except ComercialApiError as exc:
        st.error(exc.user_message)
        if st.button("Fechar"):
            clear_dialog_state(scope, id_venda)
            st.rerun()
        return

    col_valor, col_data, col_status = st.columns(3)
    col_valor.metric("Valor total", f"R$ {venda.valor_total:.2f}")
    col_data.metric(
        "Data da venda", venda.data_venda.strftime("%d/%m/%Y") if venda.data_venda else "-"
    )
    try:
        contas = financeiro_client.list_contas_receber(limit=500)
        conta = next((c for c in contas if c.id_venda == id_venda), None)
    except FinanceiroApiError:
        conta = None
    if conta is not None:
        col_status.metric(
            "Recebimento", STATUS_RECEBIMENTO.get(conta.status, conta.status)
        )
        if conta.saldo:
            st.caption(f"Saldo a receber: R$ {float(conta.saldo):.2f} · vencimento {conta.vencimento}")
    else:
        col_status.metric("Recebimento", "—")

    try:
        produto_por_id = {p.id_produto: produto_label(p) for p in client.list_produto_options()}
    except ComercialApiError:
        produto_por_id = {}

    st.caption("Itens")
    st.dataframe(
        itens_venda_df(venda.itens, produto_por_id), use_container_width=True, hide_index=True
    )

    if st.button("Fechar", use_container_width=True):
        clear_dialog_state(scope, id_venda)
        st.rerun()
