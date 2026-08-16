"""Invoice (nota fiscal) dialogs for purchase orders."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from app.compras.schemas.purchase_invoice import PurchaseInvoiceCreateSchema
from components.compras.dialog_state import clear_dialog_state, open_dialog
from components.shared.formatters import format_money
from components.shared.screens import toast_error, toast_ok
from services.compras_client import PurchasesClient


def render_invoices_section(client: PurchasesClient, order_id: int) -> None:
    st.markdown("##### Notas fiscais")
    try:
        invoices = client.list_invoices(order_id)
    except Exception as exc:
        st.warning(f"Nao foi possivel carregar notas fiscais: {exc}")
        return
    if invoices:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Numero": inv.numero,
                        "Serie": inv.serie,
                        "Emissao": inv.data_emissao.isoformat(),
                        "Valor": format_money(float(inv.valor_total)),
                    }
                    for inv in invoices
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("Nenhuma nota fiscal registrada.")
    if st.button("Registrar NF", key=f"new_invoice_{order_id}"):
        open_dialog("pedidos", "invoice", order_id)
        st.rerun()


@st.dialog("Registrar nota fiscal", width="large")
def dialog_new_invoice(client: PurchasesClient, order_id: int) -> None:
    numero = st.text_input("Numero")
    serie = st.text_input("Serie", value="1")
    data_emissao = st.date_input("Data de emissao", value=date.today())
    valor_total = st.number_input("Valor total", min_value=0.01, step=0.01)
    chave = st.text_input("Chave de acesso (opcional)", value="")

    col_cancel, _, col_save = st.columns([1, 3, 1])
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            clear_dialog_state("pedidos", order_id)
            st.rerun()
    with col_save:
        if st.button("Salvar", type="primary", use_container_width=True):
            try:
                client.create_invoice(
                    order_id,
                    PurchaseInvoiceCreateSchema(
                        numero=numero.strip(),
                        serie=serie.strip(),
                        data_emissao=data_emissao,
                        valor_total=float(valor_total),
                        chave_acesso=chave.strip() or None,
                    ),
                )
                clear_dialog_state("pedidos", order_id)
                toast_ok("Nota fiscal registrada.")
                st.rerun()
            except Exception as exc:
                toast_error(exc)
