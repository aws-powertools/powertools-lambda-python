from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
)

app = APIGatewayRestResolver(enable_validation=True)


@app.get("/openapi_schema")
def openapi_schema():
    return app.get_openapi_json_schema(
        title="Powertools e2e API",
        version="1.0.0",
        description="This is a sample Powertools e2e API",
        openapi_extensions={"x-amazon-apigateway-gateway-responses": {"DEFAULT_4XX"}},
    )


def lambda_handler(event, context):
    return app.resolve(event, context)
