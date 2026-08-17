"""Testes do conector AgroDoc/CEPEA com HTTP mockado (sem chamadas de rede reais)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest
import requests

from app.integrations.agrodoc import AgroDocClient
from app.integrations.exceptions import IntegrationHttpError, IntegrationValidationError
from app.integrations.schemas import MarketPriceData

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
def client() -> AgroDocClient:
    return AgroDocClient()


def _payload(**overrides) -> dict:
    base = {
        "boi_gordo_cepea_sp": 365.10,
        "vaca_gorda": 310.33,
        "soja": 128.00,
        "milho": 66.81,
        "bezerro_ms": 3372.00,
        "atualizado": "2026-04-18T09:30:00-04:00",
        "fonte": "CEPEA/ESALQ",
    }
    base.update(overrides)
    return base


def test_fetch_maps_all_commodities_to_market_price_data(client: AgroDocClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, _payload())
        result = client.fetch()

    assert result == [
        MarketPriceData(
            product="Boi Gordo CEPEA/SP",
            price=Decimal("365.10"),
            unit="R$/arroba",
            source="CEPEA/ESALQ",
            updated_at="2026-04-18T09:30:00-04:00",
        ),
        MarketPriceData(
            product="Vaca Gorda",
            price=Decimal("310.33"),
            unit="R$/arroba",
            source="CEPEA/ESALQ",
            updated_at="2026-04-18T09:30:00-04:00",
        ),
        MarketPriceData(
            product="Soja",
            price=Decimal("128.00"),
            unit="Reais/saca",
            source="CEPEA/ESALQ",
            updated_at="2026-04-18T09:30:00-04:00",
        ),
        MarketPriceData(
            product="Milho",
            price=Decimal("66.81"),
            unit="Reais/saca",
            source="CEPEA/ESALQ",
            updated_at="2026-04-18T09:30:00-04:00",
        ),
        MarketPriceData(
            product="Bezerro MS",
            price=Decimal("3372.00"),
            unit="R$/cabeça",
            source="CEPEA/ESALQ",
            updated_at="2026-04-18T09:30:00-04:00",
        ),
    ]


def test_fetch_calls_cotacao_endpoint_without_params_when_no_uf(client: AgroDocClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, _payload())
        client.fetch()

    args, kwargs = mock_request.call_args
    assert args[0] == "GET"
    assert args[1] == "https://agrodocai.com.br/api/v1/cotacao"
    assert kwargs["params"] is None


def test_fetch_sends_uf_param_and_includes_extra_quote(client: AgroDocClient) -> None:
    payload = _payload(boi_gordo_uf={"uf": "MS", "preco": 360.00, "praca": "MS C. Grande"})

    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, payload)
        result = client.fetch(uf="MS")

    _, kwargs = mock_request.call_args
    assert kwargs["params"] == {"uf": "MS"}
    assert result[-1] == MarketPriceData(
        product="Boi Gordo MS",
        price=Decimal("360.00"),
        unit="R$/arroba",
        source="MS C. Grande",
        updated_at="2026-04-18T09:30:00-04:00",
    )


def test_fetch_ignores_missing_uf_quote_without_error(client: AgroDocClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, _payload())
        result = client.fetch(uf="MS")

    assert len(result) == 5
    assert all(quote.product != "Boi Gordo MS" for quote in result)


def test_fetch_raises_validation_error_on_invalid_json(client: AgroDocClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, json_error=ValueError("bad json"))
        with pytest.raises(IntegrationValidationError):
            client.fetch()


def test_fetch_raises_validation_error_when_no_known_field_present(client: AgroDocClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, {"atualizado": "2026-04-18T09:30:00-04:00"})
        with pytest.raises(IntegrationValidationError):
            client.fetch()


def test_fetch_raises_http_error_on_status_500(client: AgroDocClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(500, {})
        with pytest.raises(IntegrationHttpError):
            client.fetch()


def test_fetch_raises_http_error_on_network_error(client: AgroDocClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.side_effect = requests.ConnectionError("boom")
        with pytest.raises(IntegrationHttpError):
            client.fetch()
