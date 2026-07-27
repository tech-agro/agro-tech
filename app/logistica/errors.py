"""Logistics domain business-rule errors."""


class LogisticsError(Exception):
    """Raised when a logistics business rule is violated."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
