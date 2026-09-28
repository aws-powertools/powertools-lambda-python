import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from aws_lambda_powertools.utilities.auth_alpha import AuthErrorContext, JWTVerifier
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayHttpResolver()
logger = Logger()
verifier = JWTVerifier(
    issuer=os.environ["ISSUER_URL"],
    audience=os.environ["RESOURCE_URL"],
    algorithms=["RS256"],
    required_claims=["sub", "tenant"],
    expected_claims={"token_use": "access"},
)


def on_error(error: AuthErrorContext) -> Response:
    logger.warning("Authorization failed", reason=error.reason.value, retryable=error.retryable)
    return Response(
        status_code=error.status_code,
        content_type="application/json",
        body={"message": "Access denied"},
        headers=error.headers,
    )


def belongs_to_example_tenant(claims: dict) -> bool:
    return claims["tenant"] == "example"


@app.get(
    "/orders",
    middlewares=[
        verifier.require(
            scopes=["orders:read"],
            authorize=belongs_to_example_tenant,
            on_error=on_error,
        ),
    ],
)
def list_orders():
    return {"subject": app.context["claims"]["sub"], "orders": []}


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
