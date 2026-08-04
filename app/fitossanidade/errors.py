"""Phytosanitary domain business-rule errors."""


class PhytosanitaryError(Exception):
    """Raised when a phytosanitary business rule is violated."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
