from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
)
from aws_lambda_powertools.event_handler.openapi.models import (
    OAuth2,
    OAuthFlowAuthorizationCode,
    OAuthFlows,
)
from aws_lambda_powertools.event_handler.openapi.swagger_ui import OAuth2Config

tracer = Tracer()
logger = Logger()

oauth2 = OAuth2Config(
    client_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    app_name="OAuth2 app",
)

app = APIGatewayRestResolver(enable_validation=True)
app.enable_swagger(
    oauth2_config=oauth2,
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
    security=[{"oauth": []}],
)


@app.get("/")
def hello() -> str:
    return "world"


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
