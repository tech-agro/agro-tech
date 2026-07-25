"""DataFrame para a listagem de locais de armazenamento."""

from __future__ import annotations

import pandas as pd


def locais_df(locais) -> pd.DataFrame:
    columns = ["ID", "Descrição", "Capacidade"]
    if not locais:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": local.id_local,
                "Descrição": local.descricao,
                "Capacidade": f"{local.capacidade:.2f}" if local.capacidade is not None else "-",
            }
            for local in locais
        ]
    )