"""DataFrame para a listagem de lotes."""

from __future__ import annotations

import pandas as pd


def lotes_df(lotes) -> pd.DataFrame:
    columns = ["ID", "Código", "Produto", "Validade", "Qualidade"]
    if not lotes:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": l.id_lote,
                "Código": l.codigo_lote,
                "Produto": l.produto_nome or f"#{l.id_produto}",
                "Validade": l.validade.strftime("%d/%m/%Y") if l.validade else "",
                "Qualidade": l.qualidade or "",
            }
            for l in lotes
        ]
    )