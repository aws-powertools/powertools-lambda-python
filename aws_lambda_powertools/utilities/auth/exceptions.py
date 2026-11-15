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
    TOKEN_EXCHANGE_FAILED = "token_exchange_failed"  # nosec B105
    DOWNSTREAM_REQUEST_FAILED = "downstream_request_failed"


class AuthError(Exception):
    """Base error with a fixed message that never includes credential material."""

    message = "Authentication failed"
    reason = AuthFailureReason.INVALID_TOKEN
    retryable = False

    def __init__(self) -> None:
        super().__init__(self.message)
