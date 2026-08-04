"""Open-Meteo weather connector — issue #75.

Docs: https://open-meteo.com/en/docs
"""

from __future__ import annotations

from app.integrations.base import BaseApiClient
from app.integrations.schemas import WeatherData


class OpenMeteoClient(BaseApiClient):
    """Fetch weather and map it to ``WeatherData``."""

    provider = "open-meteo"
    base_url = "https://api.open-meteo.com/v1"

    def fetch(self, latitude: float, longitude: float) -> WeatherData:
        # TODO(#75): GET forecast / current weather, map JSON → WeatherData
        raise NotImplementedError("OpenMeteoClient.fetch is not implemented yet")
