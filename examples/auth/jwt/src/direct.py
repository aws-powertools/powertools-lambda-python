import os

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.auth.jwt.exceptions import InvalidTokenError, JWKSFetchError
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayHttpResolver()
verifier = JWTVerifier(
    issuer=os.environ["ISSUER_URL"],
    audience=os.environ["RESOURCE_URL"],
    algorithms=["RS256"],
    required_claims=["sub"],
)


@app.get("/orders")
def list_orders():
    authorization = app.current_event.headers.get("authorization", "")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return Response(status_code=401, body={"message": "Unauthorized"}, headers={"WWW-Authenticate": "Bearer"})

    try:
        claims = verifier.verify(parts[1])
    except InvalidTokenError:
        return Response(
            status_code=401,
            body={"message": "Unauthorized"},
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except JWKSFetchError:
        return Response(status_code=503, body={"message": "Service Unavailable"})

    return {"subject": claims["sub"], "orders": []}


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
