"""Credential-free errors raised by JWT verification."""

from aws_lambda_powertools.utilities.auth_alpha.exceptions import AuthError, AuthFailureReason

__all__ = [
    "AuthError",
    "AuthFailureReason",
    "InvalidTokenError",
    "InvalidClaimsError",
    "TokenExpiredError",
    "InvalidSignatureError",
    "JWKSFetchError",
]


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
