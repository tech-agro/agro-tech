"""DataFrames para a listagem de vendas e seus itens."""

from __future__ import annotations

import pandas as pd


def vendas_df(vendas, cliente_por_id: dict[int, str] | None = None) -> pd.DataFrame:
    cliente_por_id = cliente_por_id or {}
    columns = ["ID", "Cliente", "Valor total", "Data da venda"]
    if not vendas:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": v.id_venda,
                "Cliente": cliente_por_id.get(v.id_cliente, f"#{v.id_cliente}"),
                "Valor total": float(v.valor_total),
                "Data da venda": v.data_venda.strftime("%d/%m/%Y") if v.data_venda else "",
            }
            for v in vendas
        ]
    )


def itens_venda_df(itens, produto_por_id: dict[int, str] | None = None) -> pd.DataFrame:
    produto_por_id = produto_por_id or {}
    columns = ["Produto", "Lote", "Quantidade", "Valor unitário"]
    if not itens:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "Produto": produto_por_id.get(i.id_produto, f"#{i.id_produto}"),
                "Lote": f"#{i.id_lote}" if i.id_lote else "-",
                "Quantidade": float(i.quantidade),
                "Valor unitário": float(i.valor_unitario),
            }
            for i in itens
        ]
    )
