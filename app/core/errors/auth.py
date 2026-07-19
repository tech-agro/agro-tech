class LoginNotAuthorizedError(Exception):
    """No registered person matches the identity returned by the login provider."""


class InactiveUserError(Exception):
    """The user exists but is deactivated."""
