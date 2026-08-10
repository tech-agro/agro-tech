"""Tests for the ViaCEP connector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.integrations.exceptions import (
    IntegrationHttpError,
    IntegrationNotFoundError,
    IntegrationValidationError,
)
from app.integrations.viacep import ViaCepClient

pytestmark = pytest.mark.unit


@pytest.fixture
def client() -> ViaCepClient:
    return ViaCepClient()


def test_normalize_cep_accepts_masked_input(client: ViaCepClient) -> None:
    assert client.normalize_cep("01001-000") == "01001000"


def test_normalize_cep_rejects_invalid_length(client: ViaCepClient) -> None:
    with pytest.raises(IntegrationValidationError, match="8 digits"):
        client.normalize_cep("123")


def test_fetch_maps_successful_response(client: ViaCepClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "cep": "01001-000",
        "logradouro": "Praça da Sé",
        "complemento": "lado ímpar",
        "bairro": "Sé",
        "localidade": "São Paulo",
        "uf": "SP",
    }

    with patch.object(client, "get", return_value=mock_response) as mock_get:
        result = client.fetch("01001-000")

    mock_get.assert_called_once_with("https://viacep.com.br/ws/01001000/json/")
    assert result.cep == "01001-000"
    assert result.logradouro == "Praça da Sé"
    assert result.bairro == "Sé"
    assert result.localidade == "São Paulo"
    assert result.uf == "SP"


def test_fetch_maps_city_level_cep_without_street(client: ViaCepClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "cep": "48570-000",
        "logradouro": "",
        "complemento": "",
        "bairro": "",
        "localidade": "Santa Brígida",
        "uf": "BA",
    }

    with patch.object(client, "get", return_value=mock_response):
        result = client.fetch("48570000")

    assert result.cep == "48570-000"
    assert result.logradouro is None
    assert result.bairro is None
    assert result.localidade == "Santa Brígida"
    assert result.uf == "BA"


def test_fetch_raises_not_found_when_provider_returns_erro(client: ViaCepClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"erro": True}

    with patch.object(client, "get", return_value=mock_response):
        with pytest.raises(IntegrationNotFoundError, match="not found"):
            client.fetch("99999999")


def test_fetch_raises_validation_error_for_invalid_json(client: ViaCepClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("invalid json")

    with patch.object(client, "get", return_value=mock_response):
        with pytest.raises(IntegrationValidationError, match="invalid JSON"):
            client.fetch("01001000")


def test_get_raises_http_error_on_bad_status(client: ViaCepClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 503

    with patch("app.integrations.base.requests.request", return_value=mock_response):
        with pytest.raises(IntegrationHttpError, match="HTTP 503"):
            client.get("https://viacep.com.br/ws/01001000/json/")
