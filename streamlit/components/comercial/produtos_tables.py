"""DataFrame para a listagem de produtos."""

from __future__ import annotations

import pandas as pd


def produtos_df(produtos) -> pd.DataFrame:
    columns = ["ID", "Nome", "Tipo", "Preço"]
    if not produtos:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": p.id_produto,
                "Nome": p.nome,
                "Tipo": p.tipo or "",
                "Preço": float(p.preco) if p.preco is not None else None,
            }
            for p in produtos
        ]
    )
