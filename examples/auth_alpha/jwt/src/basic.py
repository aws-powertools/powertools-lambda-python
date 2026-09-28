import os

from aws_lambda_powertools.utilities.auth_alpha import JWTVerifier
from aws_lambda_powertools.utilities.typing import LambdaContext

verifier = JWTVerifier(
    issuer=os.environ["ISSUER_URL"],
    audience=os.environ["RESOURCE_URL"],
    algorithms=["RS256"],
    required_claims=["sub"],
    # Adapt this constraint to your provider's access-token profile.
    expected_claims={"token_use": "access"},
)


def lambda_handler(event: dict, context: LambdaContext):
    claims = verifier.verify(event["access_token"])
    return {"subject": claims["sub"]}
