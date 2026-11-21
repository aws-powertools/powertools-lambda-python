"""Errors raised by the request signer. Messages never include credential material."""

from aws_lambda_powertools.utilities.auth.exceptions import AuthError, AuthFailureReason

__all__ = ["AuthError", "AuthFailureReason", "SignerConfigError"]


class SignerConfigError(AuthError):
    """The signer cannot sign: no region, no credentials, or a missing optional dependency.

    Raised at construction, before any request is signed, so a misconfigured function
    fails on the first cold start instead of sending unsigned requests.
    """

    message = "Request signer is not configured"
    reason = AuthFailureReason.SIGNER_MISCONFIGURED

    def __init__(self, detail: str) -> None:
        self.message = f"{SignerConfigError.message}: {detail}"
        super().__init__()
