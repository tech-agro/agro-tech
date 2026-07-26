"""DataFrame para a listagem de certificações de lote."""

from __future__ import annotations

import pandas as pd

from components.estoque.formatters import STATUS_LABELS


def certificacoes_df(certificacoes) -> pd.DataFrame:
    columns = ["ID", "Certificação", "Lote", "Emissão", "Validade", "Número", "Status"]
    if not certificacoes:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(
        [
            {
                "ID": c.id_cert_lote,
                "Certificação": c.certificacao_nome or f"#{c.id_certificacao}",
                "Lote": c.lote_codigo or f"#{c.id_lote}",
                "Emissão": c.dt_emissao.strftime("%d/%m/%Y") if c.dt_emissao else "",
                "Validade": c.dt_validade.strftime("%d/%m/%Y") if c.dt_validade else "",
                "Número": c.numero_certificado or "",
                "Status": STATUS_LABELS.get(c.status, c.status.value),
            }
            for c in certificacoes
        ]
    )