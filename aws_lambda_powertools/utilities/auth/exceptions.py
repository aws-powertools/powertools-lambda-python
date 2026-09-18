"""Credential-free errors raised by the Auth utility."""

from enum import Enum


class AuthFailureReason(str, Enum):
    """Stable, credential-free reasons suitable for application logs and metrics."""

    MISSING_TOKEN = "missing_token"  # nosec B105
    INVALID_TOKEN = "invalid_token"  # nosec B105
    INVALID_CLAIMS = "invalid_claims"
    TOKEN_EXPIRED = "token_expired"  # nosec B105
    INVALID_SIGNATURE = "invalid_signature"
    INSUFFICIENT_SCOPE = "insufficient_scope"
    FORBIDDEN = "forbidden"
    JWKS_UNAVAILABLE = "jwks_unavailable"


class AuthError(Exception):
    """Base error with a fixed message that never includes credential material."""

    message = "Authentication failed"
    reason = AuthFailureReason.INVALID_TOKEN
    retryable = False

    def __init__(self) -> None:
        super().__init__(self.message)


class InvalidTokenError(AuthError):
    """The bearer token could not be verified."""

    message = "Invalid access token"


class InvalidClaimsError(InvalidTokenError):
    """A required claim is missing or a claim does not match the token profile."""

    message = "Invalid access token claims"
    reason = AuthFailureReason.INVALID_CLAIMS


class TokenExpiredError(InvalidTokenError):
    """The access token has expired beyond the configured clock tolerance."""

    message = "Access token expired"
    reason = AuthFailureReason.TOKEN_EXPIRED


class InvalidSignatureError(InvalidTokenError):
    """The access token signature does not match the configured signing key."""

    message = "Invalid access token signature"
    reason = AuthFailureReason.INVALID_SIGNATURE


class JWKSFetchError(AuthError):
    """Required signing keys could not be retrieved or refreshed."""

    message = "Unable to retrieve verification keys"
    reason = AuthFailureReason.JWKS_UNAVAILABLE
    retryable = True
