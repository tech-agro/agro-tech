"""Purchase domain business-rule errors."""


class PurchaseError(Exception):
    """Raised when a purchase business rule is violated."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
