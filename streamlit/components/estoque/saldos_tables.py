"""DataFrame para a listagem de saldos de estoque."""

from __future__ import annotations

import pandas as pd


def saldos_df(saldos) -> pd.DataFrame:
    columns = ["ID", "Produto", "Quantidade atual"]
    if not saldos:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": s.id_saldo,
                "Produto": s.produto_nome or f"#{s.id_produto}",
                "Quantidade atual": f"{s.quantidade_atual:.2f}",
            }
            for s in saldos
        ]
    )