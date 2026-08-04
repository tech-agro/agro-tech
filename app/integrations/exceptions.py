"""Errors raised by external API connectors."""


class IntegrationError(Exception):
    """Base error for external integrations."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class IntegrationHttpError(IntegrationError):
    """HTTP call failed or returned an unexpected status."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        provider: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.provider = provider
        super().__init__(message)


class IntegrationNotFoundError(IntegrationError):
    """Requested resource was not found at the provider."""


class IntegrationValidationError(IntegrationError):
    """Provider payload could not be validated or mapped."""
