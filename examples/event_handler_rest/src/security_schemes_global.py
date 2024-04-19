from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
)
from aws_lambda_powertools.event_handler.openapi.models import (
    OAuth2,
    OAuthFlowAuthorizationCode,
    OAuthFlows,
)

tracer = Tracer()
logger = Logger()

app = APIGatewayRestResolver(enable_validation=True)


@app.get("/")
def helloworld() -> dict:
    return {"hello": "world"}


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)


if __name__ == "__main__":
    print(
        app.get_openapi_json_schema(
            title="My API",
            security_schemes={
                "oauth": OAuth2(
                    flows=OAuthFlows(
                        authorizationCode=OAuthFlowAuthorizationCode(
                            authorizationUrl="https://xxx.amazoncognito.com/oauth2/authorize",
                            tokenUrl="https://xxx.amazoncognito.com/oauth2/token",
                        ),
                    ),
                ),
            },
            security=[{"oauth": ["admin"]}],  # (1)!
        ),
    )
