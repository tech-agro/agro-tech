"""BrasilAPI CNPJ connector — issue #78.

Docs: https://brasilapi.com.br/docs#tag/CNPJ
"""

from __future__ import annotations

import re

from app.integrations.base import BaseApiClient
from app.integrations.exceptions import (
    IntegrationHttpError,
    IntegrationNotFoundError,
    IntegrationValidationError,
)
from app.integrations.schemas import CompanyData

_CNPJ_DIGITS_RE = re.compile(r"\D")
_SITUACAO_LABELS = {
    1: "NULA",
    2: "ATIVA",
    3: "SUSPENSA",
    4: "INAPTA",
    8: "BAIXADA",
}


def _normalize_cnpj(cnpj: str) -> str:
    digits = _CNPJ_DIGITS_RE.sub("", cnpj or "")
    if len(digits) != 14:
        raise IntegrationValidationError(
            f"CNPJ invalido: esperado 14 digitos, recebido {len(digits)}."
        )
    return digits


class BrasilApiCnpjClient(BaseApiClient):
    """Fetch company data by CNPJ and map it to ``CompanyData``."""

    provider = "brasilapi"
    base_url = "https://brasilapi.com.br/api/cnpj/v1"
    default_headers = {
        "User-Agent": "agro-tech/1.0 (+https://github.com/tech-agro/agro-tech)"
    }

    def fetch(self, cnpj: str) -> CompanyData:
            cnpj_normalizado = _normalize_cnpj(cnpj)

            try:
                response = self.get(f"{self.base_url}/{cnpj_normalizado}")
            except IntegrationHttpError as exc:
                if exc.status_code == 404:
                    raise IntegrationNotFoundError(
                        f"CNPJ {cnpj_normalizado} nao encontrado na BrasilAPI."
                    ) from exc
                raise

            try:
                payload = response.json()
            except ValueError as exc:
                raise IntegrationValidationError(
                    f"Resposta da BrasilAPI nao e um JSON valido: {exc}"
                ) from exc

            return self._map(payload, cnpj_normalizado)
    
    @staticmethod
    def _map(data: dict, cnpj_normalizado: str) -> CompanyData:
        razao_social = data.get("razao_social")
        if not razao_social:
            raise IntegrationValidationError(
                "Resposta da BrasilAPI sem razao_social."
            )

        situacao_codigo = data.get("situacao_cadastral") or data.get("codigo_situacao_cadastral")
        situacao = data.get("descricao_situacao_cadastral")
        if not situacao and isinstance(situacao_codigo, int):
            situacao = _SITUACAO_LABELS.get(situacao_codigo)

        try:
            return CompanyData(
                cnpj=data.get("cnpj") or cnpj_normalizado,
                razao_social=razao_social,
                nome_fantasia=data.get("nome_fantasia") or None,
                situacao_cadastral=situacao,
                cep=data.get("cep"),
                logradouro=data.get("logradouro") or None,
                numero=data.get("numero") or None,
                bairro=data.get("bairro") or None,
                municipio=data.get("municipio") or None,
                uf=data.get("uf") or None,
            )
        except Exception as exc:
            raise IntegrationValidationError(
                f"Falha ao mapear resposta da BrasilAPI para CompanyData: {exc}"
            ) from exc