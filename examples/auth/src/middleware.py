import os

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayHttpResolver()
verifier = JWTVerifier(
    issuer=os.environ["ISSUER_URL"],
    audience=os.environ["RESOURCE_URL"],
    algorithms=["RS256"],
    required_claims=["sub"],
)


@app.get("/orders", middlewares=[verifier.require(scopes=["orders:read"])])
def list_orders():
    return {"subject": app.context["claims"]["sub"], "orders": []}


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
