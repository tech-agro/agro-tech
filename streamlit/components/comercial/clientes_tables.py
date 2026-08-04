"""DataFrame para a listagem de clientes."""

from __future__ import annotations

import pandas as pd

from components.comercial.formatters import STATUS_CLIENTE_LABELS


def clientes_df(clientes) -> pd.DataFrame:
    columns = ["ID", "Cliente", "Status"]
    if not clientes:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": c.id_cliente,
                "Cliente": c.pessoa_nome or f"#{c.id_pessoa}",
                "Status": STATUS_CLIENTE_LABELS.get(c.status, c.status.value),
            }
            for c in clientes
        ]
    )
