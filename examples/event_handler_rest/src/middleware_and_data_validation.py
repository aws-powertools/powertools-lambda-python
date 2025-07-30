from __future__ import annotations

from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware

app = APIGatewayRestResolver(enable_validation=True)


def auth_middleware(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
    # This 401 response won't trigger validation errors
    return Response(status_code=401, content_type="application/json", body="{}")


app.use(middlewares=[auth_middleware])


@app.get("/protected")
def protected_route() -> list[str]:
    # Only this response will be validated against OpenAPI schema
    return ["protected", "route"]
