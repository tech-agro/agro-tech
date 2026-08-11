"""DataFrame for the suppliers listing."""

from __future__ import annotations

import pandas as pd


def fornecedores_df(suppliers) -> pd.DataFrame:
    columns = ["ID", "Nome", "Documento", "Categoria"]
    if not suppliers:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": s.id_fornecedor,
                "Nome": s.nome,
                "Documento": s.documento,
                "Categoria": s.categoria or "—",
            }
            for s in suppliers
        ]
    )
