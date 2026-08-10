"""ViaCEP address connector — issue #77.

Docs: https://viacep.com.br/
"""

from __future__ import annotations

import re
from typing import Any

from app.integrations.base import BaseApiClient
from app.integrations.exceptions import (
    IntegrationNotFoundError,
    IntegrationValidationError,
)
from app.integrations.schemas import AddressData

_CEP_DIGITS_RE = re.compile(r"\D")


class ViaCepClient(BaseApiClient):
    """Fetch address by CEP and map it to ``AddressData``."""

    provider = "viacep"
    base_url = "https://viacep.com.br/ws"
    timeout = 20.0

    @staticmethod
    def normalize_cep(cep: str) -> str:
        """Return CEP with digits only; raise if not exactly 8 digits."""
        digits = _CEP_DIGITS_RE.sub("", cep.strip())
        if len(digits) != 8 or not digits.isdigit():
            raise IntegrationValidationError("CEP must contain exactly 8 digits.")
        return digits

    @staticmethod
    def format_cep(cep: str) -> str:
        """Format normalized CEP as #####-###."""
        normalized = ViaCepClient.normalize_cep(cep)
        return f"{normalized[:5]}-{normalized[5:]}"

    def fetch(self, cep: str) -> AddressData:
        normalized = self.normalize_cep(cep)
        url = f"{self.base_url}/{normalized}/json/"
        response = self.get(url)

        try:
            payload = response.json()
        except ValueError as exc:
            raise IntegrationValidationError(
                "ViaCEP returned an invalid JSON payload."
            ) from exc

        if not isinstance(payload, dict):
            raise IntegrationValidationError(
                "ViaCEP returned an unexpected response format."
            )

        if payload.get("erro"):
            raise IntegrationNotFoundError(f"CEP {normalized} not found.")

        return self._map_payload(payload, fallback_cep=normalized)

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @classmethod
    def _map_payload(cls, payload: dict[str, Any], *, fallback_cep: str) -> AddressData:
        cep = cls._clean_text(payload.get("cep")) or cls.format_cep(fallback_cep)
        try:
            return AddressData(
                cep=cep,
                logradouro=cls._clean_text(payload.get("logradouro")),
                complemento=cls._clean_text(payload.get("complemento")),
                bairro=cls._clean_text(payload.get("bairro")),
                localidade=cls._clean_text(payload.get("localidade")),
                uf=cls._clean_text(payload.get("uf")),
            )
        except ValueError as exc:
            raise IntegrationValidationError(
                "ViaCEP payload could not be mapped to AddressData."
            ) from exc
