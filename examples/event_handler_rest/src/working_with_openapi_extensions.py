from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.models import APIKey, APIKeyIn, Server

app = APIGatewayRestResolver(enable_validation=True)

servers = Server(
    url="http://example.com",
    description="Example server",
    openapi_extensions={"x-amazon-apigateway-endpoint-configuration": {"vpcEndpoint": "myendpointid"}},  # (1)!
)


@app.get(
    "/hello",
    openapi_extensions={"x-amazon-apigateway-integration": {"type": "aws", "uri": "my_lambda_arn"}},  # (2)!
)
def hello():
    return app.get_openapi_json_schema(
        servers=[servers],
        security_schemes={
            "apikey": APIKey(
                name="X-API-KEY",
                description="API KeY",
                in_=APIKeyIn.header,
                openapi_extensions={"x-amazon-apigateway-authorizer": "custom"},  # (3)!
            ),
        },
        openapi_extensions={"x-amazon-apigateway-gateway-responses": {"DEFAULT_4XX"}},  # (4)!
    )


def lambda_handler(event, context):
    return app.resolve(event, context)
