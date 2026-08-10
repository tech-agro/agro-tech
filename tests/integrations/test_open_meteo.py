"""Testes do conector Open-Meteo com HTTP mockado (sem chamadas de rede reais)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import requests

from app.integrations.exceptions import IntegrationHttpError, IntegrationValidationError
from app.integrations.open_meteo import OpenMeteoClient
from app.integrations.schemas import WeatherData


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
def client() -> OpenMeteoClient:
    return OpenMeteoClient()


def test_fetch_maps_json_to_weather_data(client: OpenMeteoClient) -> None:
    payload = {
        "latitude": -8.05,
        "longitude": -34.9,
        "current": {
            "time": "2026-08-09T12:00",
            "temperature_2m": 27.4,
            "relative_humidity_2m": 61,
            "precipitation": 0.2,
        },
    }
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, payload)
        result = client.fetch(latitude=-8.05, longitude=-34.9)

    assert result == WeatherData(
        temperature_c=27.4,
        humidity_pct=61,
        precipitation_mm=0.2,
        latitude=-8.05,
        longitude=-34.9,
    )


def test_fetch_calls_forecast_endpoint_with_expected_params(client: OpenMeteoClient) -> None:
    payload = {
        "latitude": 10.0,
        "longitude": 20.0,
        "current": {"temperature_2m": 1, "relative_humidity_2m": 2, "precipitation": 3},
    }
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, payload)
        client.fetch(latitude=10.0, longitude=20.0)

    args, kwargs = mock_request.call_args
    assert args[0] == "GET"
    assert args[1] == "https://api.open-meteo.com/v1/forecast"
    assert kwargs["params"] == {
        "latitude": 10.0,
        "longitude": 20.0,
        "current": "temperature_2m,relative_humidity_2m,precipitation",
    }


def test_fetch_raises_on_http_error_status(client: OpenMeteoClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(500, {})
        with pytest.raises(IntegrationHttpError):
            client.fetch(latitude=0.0, longitude=0.0)


def test_fetch_raises_on_network_error(client: OpenMeteoClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.side_effect = requests.ConnectionError("boom")
        with pytest.raises(IntegrationHttpError):
            client.fetch(latitude=0.0, longitude=0.0)


def test_fetch_raises_on_missing_current_block(client: OpenMeteoClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, {"latitude": 0.0, "longitude": 0.0})
        with pytest.raises(IntegrationValidationError):
            client.fetch(latitude=0.0, longitude=0.0)


def test_fetch_raises_on_invalid_json(client: OpenMeteoClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, json_error=ValueError("bad json"))
        with pytest.raises(IntegrationValidationError):
            client.fetch(latitude=0.0, longitude=0.0)


def test_fetch_raises_on_non_dict_payload(client: OpenMeteoClient) -> None:
    with patch("app.integrations.base.requests.request") as mock_request:
        mock_request.return_value = FakeResponse(200, [1, 2, 3])
        with pytest.raises(IntegrationValidationError):
            client.fetch(latitude=0.0, longitude=0.0)
