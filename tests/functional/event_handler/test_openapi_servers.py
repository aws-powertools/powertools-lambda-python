from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
from aws_lambda_powertools.event_handler.openapi.models import Server


def test_openapi_schema_default_server():
    app = ApiGatewayResolver()

    schema = app.get_openapi_schema(title="Hello API", version="1.0.0")
    assert schema.servers
    assert len(schema.servers) == 1
    assert schema.servers[0].url == "/"


def test_openapi_schema_custom_server():
    app = ApiGatewayResolver()

    schema = app.get_openapi_schema(
        title="Hello API",
        version="1.0.0",
        servers=[Server(url="https://example.org/", description="Example website")],
    )

    assert schema.servers
    assert len(schema.servers) == 1
    assert str(schema.servers[0].url) == "https://example.org/"
    assert schema.servers[0].description == "Example website"
