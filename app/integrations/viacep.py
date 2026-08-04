"""ViaCEP address connector — issue #77.

Docs: https://viacep.com.br/
"""

from __future__ import annotations

from app.integrations.base import BaseApiClient
from app.integrations.schemas import AddressData


class ViaCepClient(BaseApiClient):
    """Fetch address by CEP and map it to ``AddressData``."""

    provider = "viacep"
    base_url = "https://viacep.com.br/ws"

    def fetch(self, cep: str) -> AddressData:
        # TODO(#77): GET /{cep}/json/, map JSON → AddressData
        # Raise IntegrationNotFoundError when response has {"erro": true}
        raise NotImplementedError("ViaCepClient.fetch is not implemented yet")
