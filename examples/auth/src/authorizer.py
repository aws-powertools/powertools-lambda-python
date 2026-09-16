import os

from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.typing import LambdaContext

verifier = JWTVerifier(
    issuer=os.environ["ISSUER_URL"],
    audience=os.environ["RESOURCE_URL"],
    algorithms=["RS256"],
    required_claims=["sub"],
)


def iam_handler(event: dict, context: LambdaContext):
    return verifier.authorize(
        event,
        scopes=["orders:read"],
        response_format="iam",
        context_claims=["sub"],
    )


def simple_handler(event: dict, context: LambdaContext):
    return verifier.authorize(event, scopes=["orders:read"], response_format="simple")
