"""BrasilAPI CNPJ connector — issue #78.

Docs: https://brasilapi.com.br/docs#tag/CNPJ
"""

from __future__ import annotations

from app.integrations.base import BaseApiClient
from app.integrations.schemas import CompanyData


class BrasilApiCnpjClient(BaseApiClient):
    """Fetch company data by CNPJ and map it to ``CompanyData``."""

    provider = "brasilapi"
    base_url = "https://brasilapi.com.br/api/cnpj/v1"

    def fetch(self, cnpj: str) -> CompanyData:
        # TODO(#78): GET /{cnpj}, map JSON → CompanyData
        raise NotImplementedError("BrasilApiCnpjClient.fetch is not implemented yet")
