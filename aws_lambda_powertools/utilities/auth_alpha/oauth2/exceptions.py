"""Credential-free errors raised by outbound OAuth requests."""

from aws_lambda_powertools.utilities.auth_alpha.exceptions import AuthError, AuthFailureReason

__all__ = ["AuthError", "AuthFailureReason", "TokenExchangeError", "DownstreamRequestError"]


class TokenExchangeError(AuthError):
    """A usable bearer token could not be obtained.

    ``retryable`` indicates a transient endpoint failure or acquisition timeout.
    Invalid responses, rejected credentials, and secret-loader failures are not
    retried automatically. Exception messages never include provider details.
    """

    message = "Unable to acquire an access token"
    reason = AuthFailureReason.TOKEN_EXCHANGE_FAILED

    def __init__(self, *, retryable: bool = False) -> None:
        self.retryable = retryable
        super().__init__()


class DownstreamRequestError(AuthError):
    """The authenticated HTTP operation could not complete.

    The server may already have performed the operation. Callers must decide
    whether replay is safe; this error does not advise automatic retries.
    """

    message = "Authenticated request failed"
    reason = AuthFailureReason.DOWNSTREAM_REQUEST_FAILED
