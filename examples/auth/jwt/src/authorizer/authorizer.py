import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.auth.jwt.exceptions import AuthError
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
verifier = JWTVerifier(
    issuer=os.environ["ISSUER_URL"],
    audience=os.environ["RESOURCE_URL"],
    algorithms=["RS256"],
    required_claims=["sub"],
    # Adapt this constraint to the access-token profile issued by your provider.
    expected_claims={"token_use": "access"},
)


def record_failure(error: AuthError) -> None:
    # Opt-in application logging; never log the event, token, or claims.
    logger.warning("Authorization failed", reason=error.reason.value, retryable=error.retryable)


def iam_handler(event: dict, context: LambdaContext):
    return verifier.authorize(
        event,
        scopes=["orders:read"],
        response_format="iam",
        context_claims=["sub"],
        on_error=record_failure,
    )


def simple_handler(event: dict, context: LambdaContext):
    return verifier.authorize(event, scopes=["orders:read"], response_format="simple", on_error=record_failure)
