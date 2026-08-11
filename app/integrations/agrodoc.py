"""AgroDoc / CEPEA market price connector — issue #76.

Docs: https://agrodocai.com.br/api-docs
"""

from __future__ import annotations

from typing import Any

from app.integrations.base import BaseApiClient
from app.integrations.exceptions import IntegrationValidationError
from app.integrations.schemas import MarketPriceData

# (chave no payload, nome do produto, unidade) — GET /cotacao sempre retorna
# essas commodities juntas em uma unica resposta (sem filtro por produto).
_COMMODITY_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("boi_gordo_cepea_sp", "Boi Gordo CEPEA/SP", "R$/arroba"),
    ("vaca_gorda", "Vaca Gorda", "R$/arroba"),
    ("soja", "Soja", "R$/saca"),
    ("milho", "Milho", "R$/saca"),
    ("bezerro_ms", "Bezerro MS", "R$/cabeça"),
)


class AgroDocClient(BaseApiClient):
    """Fetch commodity quotes and map them to ``MarketPriceData``."""

    provider = "agrodoc"
    base_url = "https://agrodocai.com.br/api/v1"

    def fetch(self, uf: str | None = None) -> list[MarketPriceData]:
        response = self.get(f"{self.base_url}/cotacao", params={"uf": uf} if uf else None)
        payload = self._parse_json(response)
        return self._map(payload, uf=uf)

    def _parse_json(self, response: Any) -> dict:
        try:
            payload = response.json()
        except ValueError as exc:
            raise IntegrationValidationError(
                "AgroDoc retornou um payload que nao e JSON valido."
            ) from exc
        if not isinstance(payload, dict):
            raise IntegrationValidationError("AgroDoc retornou um payload com formato inesperado.")
        return payload

    @staticmethod
    def _map(payload: dict, *, uf: str | None) -> list[MarketPriceData]:
        source = payload.get("fonte")
        updated_at = payload.get("atualizado")

        try:
            quotes = [
                MarketPriceData(
                    product=produto, price=preco, unit=unidade, source=source, updated_at=updated_at
                )
                for chave, produto, unidade in _COMMODITY_FIELDS
                if (preco := payload.get(chave)) is not None
            ]

            if uf:
                boi_uf = payload.get("boi_gordo_uf")
                if isinstance(boi_uf, dict) and boi_uf.get("preco") is not None:
                    quotes.append(
                        MarketPriceData(
                            product=f"Boi Gordo {boi_uf.get('uf', uf)}",
                            price=boi_uf["preco"],
                            unit="R$/arroba",
                            source=boi_uf.get("praca") or source,
                            updated_at=updated_at,
                        )
                    )
        except Exception as exc:
            raise IntegrationValidationError(f"Falha ao mapear resposta da AgroDoc: {exc}") from exc

        if not quotes:
            raise IntegrationValidationError("Resposta da AgroDoc nao contem nenhuma cotacao reconhecida.")
        return quotes
