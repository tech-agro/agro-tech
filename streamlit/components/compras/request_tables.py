"""DataFrames for purchase request lists."""

from __future__ import annotations

import pandas as pd

from components.compras.formatters import PURCHASE_TYPE_LABELS, REQUEST_STATUS_LABELS


def requests_df(requests) -> pd.DataFrame:
    if not requests:
        return pd.DataFrame(
            columns=["ID", "Data", "Tipo", "Status", "Pedido gerado"]
        )
    return pd.DataFrame(
        [
            {
                "ID": r.id_solicitacao,
                "Data": r.data_solicitacao.isoformat(),
                "Tipo": PURCHASE_TYPE_LABELS.get(r.tipo_compra, r.tipo_compra.value),
                "Status": REQUEST_STATUS_LABELS.get(r.status, r.status.value),
                "Pedido gerado": f"#{r.id_pedido}" if r.id_pedido else "—",
            }
            for r in requests
        ]
    )


def request_items_view_df(items) -> pd.DataFrame:
    columns = ["ID produto", "Produto", "Quantidade", "Unidade de medida"]
    if not items:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID produto": i.id_produto,
                "Produto": i.produto_nome or f"#{i.id_produto}",
                "Quantidade": float(i.quantidade),
                "Unidade de medida": i.unidade_sigla or "—",
            }
            for i in items
        ]
    )
