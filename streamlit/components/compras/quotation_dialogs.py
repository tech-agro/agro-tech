"""Quotation comparison and supplier selection dialogs."""

from __future__ import annotations

import streamlit as st

from app.compras.schemas.lookups import ProductOptionSchema, SupplierOptionSchema
from app.compras.schemas.quotation_item import QuotationItemCreateSchema
from components.compras.dialog_state import clear_dialog_state
from components.compras.formatters import product_label, supplier_label
from components.shared.formatters import format_money
from components.shared.screens import toast_error, toast_ok
from services.compras_client import PurchasesClient


@st.dialog("Cotacoes de fornecedores", width="large")
def dialog_quotations(
    client: PurchasesClient,
    request_id: int,
    suppliers: list[SupplierOptionSchema],
    products: list[ProductOptionSchema],
) -> None:
    try:
        comparison = client.get_quotation_comparison(request_id)
        quotations = client.list_quotations(request_id)
    except Exception as exc:
        toast_error(exc)
        st.stop()

    st.caption(f"Solicitacao #{request_id} — compare precos e selecione o vencedor.")

    if not quotations:
        st.info("Nenhuma cotacao registrada ainda.")
    else:
        for quotation in quotations:
            items = client.list_quotation_items(quotation.id_cotacao)
            st.markdown(
                f"**{quotation.fornecedor_nome or quotation.id_fornecedor}** "
                f"— prazo: {quotation.prazo_entrega_dias or '—'} dias "
                f"— status: {quotation.status.value}"
            )
            if items:
                st.table(
                    {
                        "Produto": [i.get("produto_nome") or i.get("id_produto") for i in items],
                        "Qtd": [i.get("quantidade") for i in items],
                        "Preco unit.": [format_money(float(i.get("preco_unitario", 0))) for i in items],
                    }
                )
            if quotation.status.value != "VENCEDORA":
                if st.button(
                    f"Selecionar vencedor (#{quotation.id_cotacao})",
                    key=f"win_{quotation.id_cotacao}",
                ):
                    try:
                        order = client.select_winning_quotation(quotation.id_cotacao)
                        clear_dialog_state("solicitacoes", request_id)
                        toast_ok(f"Cotacao vencedora! Pedido #{order.id_pedido} criado.")
                        st.rerun()
                    except Exception as exc:
                        toast_error(exc)

    st.markdown("##### Nova cotacao")
    if not suppliers or not products:
        st.warning("Cadastre fornecedores e produtos.")
        return

    supplier_map = {supplier_label(s): s.id_fornecedor for s in suppliers}
    supplier_choice = st.selectbox("Fornecedor", list(supplier_map.keys()))
    prazo = st.number_input("Prazo de entrega (dias)", min_value=0, step=1, value=7)
    st.caption("Informe preco unitario para cada produto da solicitacao.")
    quote_items: list[QuotationItemCreateSchema] = []
    for prod in comparison.produtos:
        price = st.number_input(
            f"Preco — {prod.get('produto_nome') or prod.get('id_produto')} "
            f"(qtd {prod.get('quantidade')})",
            min_value=0.0,
            step=0.01,
            key=f"quote_price_{prod.get('id_produto')}_{request_id}",
        )
        quote_items.append(
            QuotationItemCreateSchema(
                id_produto=int(prod["id_produto"]),
                quantidade=float(prod["quantidade"]),
                preco_unitario=float(price),
            )
        )

    col_cancel, _, col_save = st.columns([1, 3, 1])
    with col_cancel:
        if st.button("Fechar", use_container_width=True, key="quote_close"):
            clear_dialog_state("solicitacoes", request_id)
            st.rerun()
    with col_save:
        if st.button("Registrar cotacao", type="primary", use_container_width=True):
            try:
                client.create_quotation(
                    request_id,
                    id_fornecedor=supplier_map[supplier_choice],
                    itens=quote_items,
                    prazo_entrega_dias=int(prazo) if prazo else None,
                )
                toast_ok("Cotacao registrada.")
                st.rerun()
            except Exception as exc:
                toast_error(exc)
