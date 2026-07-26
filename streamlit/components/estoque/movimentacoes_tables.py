"""DataFrame para a listagem de movimentações de estoque."""

from __future__ import annotations

import pandas as pd

_TIPO_LABELS: dict[str, str] = {
    "entrada_compra": "Entrada (compra)",
    "entrada_colheita": "Entrada (colheita)",
    "saida_venda": "Saída (venda)",
    "saida_atividade": "Saída (atividade)",
}


def movimentacoes_df(movimentacoes) -> pd.DataFrame:
    columns = ["ID", "Produto", "Lote", "Tipo", "Quantidade", "Data"]
    if not movimentacoes:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": m.id_movimentacao,
                "Produto": m.produto_nome or f"#{m.id_produto}",
                "Lote": m.lote_codigo or "-",
                "Tipo": _TIPO_LABELS.get(m.tipo_movimentacao, m.tipo_movimentacao),
                "Quantidade": f"{m.quantidade:.2f}",
                "Data": m.data_movimentacao.strftime("%d/%m/%Y %H:%M"),
            }
            for m in movimentacoes
        ]
    )