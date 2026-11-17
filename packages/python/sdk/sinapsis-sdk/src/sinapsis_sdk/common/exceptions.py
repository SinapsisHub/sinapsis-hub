"""Exceptions raised by the Sinapsis SDK."""


class SinapsisError(Exception):
    """Base exception for all Sinapsis SDK errors."""


class ConfigurationError(SinapsisError):
    """Raised when the SDK configuration is invalid."""


class AuthenticationError(SinapsisError):
    """Raised when authentication fails."""


class AuthorizationError(SinapsisError):
    """Raised when the authenticated user is not authorized."""


class NotFoundError(SinapsisError):
    """Raised when a requested resource does not exist."""


class ValidationError(SinapsisError):
    """Raised when request or response data is invalid."""


class APIError(SinapsisError):
    """Raised when the API returns an unexpected response."""

    def __init__(self, message: str, *, status_code: int | None = None, response: object | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NetworkError(SinapsisError):
    """Raised when a network-level error occurs."""
