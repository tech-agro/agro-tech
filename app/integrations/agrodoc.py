"""AgroDoc / CEPEA market price connector — issue #76.

Docs: https://agrodocai.com.br/api-docs
"""

from __future__ import annotations

from app.integrations.base import BaseApiClient
from app.integrations.schemas import MarketPriceData


class AgroDocClient(BaseApiClient):
    """Fetch commodity quotes and map them to ``MarketPriceData``."""

    provider = "agrodoc"
    base_url = "https://agrodocai.com.br/api/v1"

    def fetch(self, product: str | None = None, uf: str | None = None) -> MarketPriceData:
        # TODO(#76): GET /cotacao, map JSON → MarketPriceData
        raise NotImplementedError("AgroDocClient.fetch is not implemented yet")
