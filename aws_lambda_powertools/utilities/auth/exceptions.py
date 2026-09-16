"""Credential-free errors raised by the Auth utility."""


class AuthError(Exception):
    """Base error with a fixed message that never includes credential material."""

    message = "Authentication failed"

    def __init__(self) -> None:
        super().__init__(self.message)


class InvalidTokenError(AuthError):
    """The bearer token could not be verified."""

    message = "Invalid access token"


class InvalidClaimsError(InvalidTokenError):
    """A required claim is missing or a claim does not match the token profile."""

    message = "Invalid access token claims"


class TokenExpiredError(InvalidTokenError):
    """The access token has expired beyond the configured clock tolerance."""

    message = "Access token expired"


class InvalidSignatureError(InvalidTokenError):
    """The access token signature does not match the configured signing key."""

    message = "Invalid access token signature"


class JWKSFetchError(AuthError):
    """Required signing keys could not be retrieved or refreshed."""

    message = "Unable to retrieve verification keys"


class TokenExchangeError(AuthError):
    """Client credentials could not be exchanged for a usable bearer token."""

    message = "Unable to acquire an access token"
