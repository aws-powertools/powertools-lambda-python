import os

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
    Response,
)
from aws_lambda_powertools.event_handler.openapi.models import (
    OAuth2,
    OAuthFlowAuthorizationCode,
    OAuthFlows,
)
from aws_lambda_powertools.event_handler.openapi.swagger_ui import OAuth2Config

tracer = Tracer()
logger = Logger()

region = os.getenv("AWS_REGION")
cognito_domain = os.getenv("COGNITO_USER_POOL_DOMAIN")

app = APIGatewayRestResolver(enable_validation=True)
app.enable_swagger(
    # NOTE: for this to work, your OAuth2 redirect url needs to precisely follow this format:
    # https://<your_api_id>.execute-api.<region>.amazonaws.com/<stage>/swagger?format=oauth2-redirect
    oauth2_config=OAuth2Config(app_name="OAuth2 Test"),
    security_schemes={
        "oauth": OAuth2(
            flows=OAuthFlows(
                authorizationCode=OAuthFlowAuthorizationCode(
                    authorizationUrl=f"https://{cognito_domain}.auth.{region}.amazoncognito.com/oauth2/authorize",
                    tokenUrl=f"https://{cognito_domain}.auth.{region}.amazoncognito.com/oauth2/token",
                ),
            ),
        ),
    },
    security=[{"oauth": []}],
)


@app.get("/")
def helloworld() -> Response[dict]:
    logger.info("Hello, World!")
    return Response(
        status_code=200,
        body={"message": "Hello, World"},
        content_type="application/json",
    )


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
