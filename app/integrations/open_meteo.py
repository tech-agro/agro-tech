"""Open-Meteo weather connector — issue #75.

Docs: https://open-meteo.com/en/docs
"""

from __future__ import annotations

from typing import Any

from app.integrations.base import BaseApiClient
from app.integrations.exceptions import IntegrationValidationError
from app.integrations.schemas import WeatherData


class OpenMeteoClient(BaseApiClient):
    """Fetch weather and map it to ``WeatherData``."""

    provider = "open-meteo"
    base_url = "https://api.open-meteo.com/v1"
    current_fields = ("temperature_2m", "relative_humidity_2m", "precipitation")

    def fetch(self, latitude: float, longitude: float) -> WeatherData:
        response = self.get(
            f"{self.base_url}/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": ",".join(self.current_fields),
            },
        )
        payload = self._parse_json(response)

        current = payload.get("current")
        if not isinstance(current, dict):
            raise IntegrationValidationError(
                "Open-Meteo response is missing the 'current' weather block."
            )

        return WeatherData(
            temperature_c=current.get("temperature_2m"),
            humidity_pct=current.get("relative_humidity_2m"),
            precipitation_mm=current.get("precipitation"),
            latitude=payload.get("latitude", latitude),
            longitude=payload.get("longitude", longitude),
        )

    def _parse_json(self, response: Any) -> dict:
        try:
            payload = response.json()
        except ValueError as exc:
            raise IntegrationValidationError(
                "Open-Meteo returned a payload that is not valid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise IntegrationValidationError(
                "Open-Meteo returned an unexpected payload shape."
            )
        return payload
