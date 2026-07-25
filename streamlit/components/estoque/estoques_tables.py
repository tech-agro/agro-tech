"""DataFrames para a listagem de estoques."""

from __future__ import annotations

import pandas as pd


def estoques_df(estoques) -> pd.DataFrame:
    columns = ["ID", "Local de armazenamento"]
    if not estoques:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": e.id_estoque,
                "Local de armazenamento": e.local_descricao or f"#{e.id_local}",
            }
            for e in estoques
        ]
    )