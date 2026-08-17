"""DataFrames for purchases list and item detail views."""

from __future__ import annotations

import pandas as pd

from components.compras.formatters import PURCHASE_TYPE_LABELS, STATUS_LABELS


def orders_df(orders) -> pd.DataFrame:
    if not orders:
        return pd.DataFrame(columns=["ID", "Fornecedor", "Tipo", "Data", "Status"])
    return pd.DataFrame(
        [
            {
                "ID": o.id_pedido,
                "Fornecedor": o.fornecedor_nome or f"#{o.id_fornecedor}",
                "Tipo": PURCHASE_TYPE_LABELS.get(
                    o.tipo_compra, getattr(o.tipo_compra, "value", "Insumo")
                ),
                "Data": o.data_pedido.isoformat() if o.data_pedido else "",
                "Status": STATUS_LABELS.get(o.status, o.status.value),
            }
            for o in orders
        ]
    )


def items_view_df(items) -> pd.DataFrame:
    columns = [
        "ID produto",
        "Produto",
        "Quantidade",
        "Unidade de medida",
        "Valor unitario",
        "Subtotal",
    ]
    if not items:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID produto": i.id_produto,
                "Produto": i.produto_nome or f"#{i.id_produto}",
                "Quantidade": float(i.quantidade),
                "Unidade de medida": i.unidade_sigla.value if i.unidade_sigla else "—",
                "Valor unitario": float(i.valor_unitario),
                "Subtotal": round(float(i.quantidade) * float(i.valor_unitario), 2),
            }
            for i in items
        ]
    )
