"""Shared HTTP client for external connectors."""

from __future__ import annotations

from typing import Any

import requests

from app.integrations.exceptions import IntegrationHttpError


class BaseApiClient:
    """Thin HTTP helper. Connector classes inherit this and only map responses."""

    provider: str = "external"
    timeout: float = 10.0
    default_headers: dict[str, str] | None = None

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        return self._request("GET", url, params=params, headers=headers)

    def post(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        return self._request(
            "POST", url, params=params, headers=headers, json=json
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> requests.Response:
        merged_headers = {**(self.default_headers or {}), **(headers or {})}
        try:
            response = requests.request(
                method,
                url,
                params=params,
                headers=merged_headers or None,
                json=json,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise IntegrationHttpError(
                f"{self.provider} request failed: {exc}",
                provider=self.provider,
            ) from exc

        if response.status_code >= 400:
            raise IntegrationHttpError(
                f"{self.provider} returned HTTP {response.status_code}",
                status_code=response.status_code,
                provider=self.provider,
            )
        return response
