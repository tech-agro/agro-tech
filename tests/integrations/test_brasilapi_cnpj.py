"""Testes do conector BrasilAPI CNPJ com HTTP mockado (sem chamadas de rede reais)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import requests

from app.integrations.brasilapi import BrasilApiCnpjClient
from app.integrations.exceptions import (
    IntegrationHttpError,
    IntegrationNotFoundError,
    IntegrationValidationError,
)
from app.integrations.schemas import CompanyData

pytestmark = pytest.mark.unit


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, json_error=None) -> None:
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._payload


@pytest.fixture
def client() -> BrasilApiCnpjClient:
    return BrasilApiCnpjClient()


def _payload(**overrides) -> dict:
    base = {
        "cnpj": "19131243000197",
        "razao_social": "OPEN KNOWLEDGE BRASIL",
        "nome_fantasia": "OK BR",
        "descricao_situacao_cadastral": "ATIVA",
        "cep": "01310100",
        "logradouro": "AVENIDA PAULISTA",
        "numero": "1000",
        "bairro": "BELA VISTA",
        "municipio": "SAO PAULO",
        "uf": "SP",
    }
    base.update(overrides)
    return base


def test_fetch_maps_json_to_company_data(client: BrasilApiCnpjClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, _payload())
        result = client.fetch("19131243000197")

    assert result == CompanyData(
        cnpj="19131243000197",
        razao_social="OPEN KNOWLEDGE BRASIL",
        nome_fantasia="OK BR",
        situacao_cadastral="ATIVA",
        cep="01310100",
        logradouro="AVENIDA PAULISTA",
        numero="1000",
        bairro="BELA VISTA",
        municipio="SAO PAULO",
        uf="SP",
    )


def test_fetch_normalizes_formatted_cnpj_before_calling_api(
    client: BrasilApiCnpjClient,
) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, _payload())
        client.fetch("19.131.243/0001-97")

    args, _ = mock_request.call_args
    assert args[1] == "https://brasilapi.com.br/api/cnpj/v1/19131243000197"


def test_fetch_uses_numeric_situacao_code_when_description_missing(
    client: BrasilApiCnpjClient,
) -> None:
    payload = _payload()
    payload.pop("descricao_situacao_cadastral")
    payload["situacao_cadastral"] = 2  # ATIVA

    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, payload)
        result = client.fetch("19131243000197")

    assert result.situacao_cadastral == "ATIVA"


def test_fetch_treats_empty_nome_fantasia_as_none(client: BrasilApiCnpjClient) -> None:
    payload = _payload(nome_fantasia="")

    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, payload)
        result = client.fetch("19131243000197")

    assert result.nome_fantasia is None


def test_fetch_raises_validation_error_on_malformed_cnpj(
    client: BrasilApiCnpjClient,
) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        with pytest.raises(IntegrationValidationError):
            client.fetch("123")

    mock_request.assert_not_called()


def test_fetch_raises_not_found_on_404(client: BrasilApiCnpjClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(404, {"message": "not found"})
        with pytest.raises(IntegrationNotFoundError):
            client.fetch("19131243000197")


def test_fetch_raises_http_error_on_other_status(client: BrasilApiCnpjClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(500, {})
        with pytest.raises(IntegrationHttpError):
            client.fetch("19131243000197")


def test_fetch_raises_http_error_on_network_error(client: BrasilApiCnpjClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.side_effect = requests.ConnectionError("boom")
        with pytest.raises(IntegrationHttpError):
            client.fetch("19131243000197")


def test_fetch_raises_validation_error_on_invalid_json(client: BrasilApiCnpjClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, json_error=ValueError("bad json"))
        with pytest.raises(IntegrationValidationError):
            client.fetch("19131243000197")


def test_fetch_raises_validation_error_when_razao_social_missing(
    client: BrasilApiCnpjClient,
) -> None:
    payload = _payload()
    payload.pop("razao_social")

    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, payload)
        with pytest.raises(IntegrationValidationError):
            client.fetch("19131243000197")