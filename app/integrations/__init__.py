"""External API connectors (HTTP clients + internal DTOs).

Each connector calls an external API, validates the response, and maps it to an
internal model. Domain services consume those models — they must not depend on
raw provider JSON.

Shared pieces:
- ``base.BaseApiClient`` — timeout, GET/POST, HTTP error handling
- ``exceptions`` — integration errors
- ``schemas`` — internal DTOs (Pydantic)

Connectors (one per person / issue):
- ``open_meteo`` — weather → Inteligência (#75)
- ``agrodoc`` — CEPEA prices → Comercial / Inteligência (#76)
- ``viacep`` — address by CEP → Logística (#77)
- ``brasilapi`` — CNPJ lookup → cadastros (#78)
"""

from app.integrations.exceptions import (
    IntegrationError,
    IntegrationHttpError,
    IntegrationNotFoundError,
    IntegrationValidationError,
)

__all__ = [
    "IntegrationError",
    "IntegrationHttpError",
    "IntegrationNotFoundError",
    "IntegrationValidationError",
]
