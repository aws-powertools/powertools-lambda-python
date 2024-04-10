import pytest

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.models import APIKey, APIKeyIn


def test_openapi_top_level_security():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema(
        security_schemes={
            "apiKey": APIKey(name="X-API-KEY", description="API Key", in_=APIKeyIn.header),
        },
        security=[{"apiKey": []}],
    )

    security = schema.security
    assert security is not None

    assert len(security) == 1
    assert security[0] == {"apiKey": []}


def test_openapi_top_level_security_missing():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    with pytest.raises(ValueError):
        app.get_openapi_schema(
            security=[{"apiKey": []}],
        )


def test_openapi_operation_security():
    app = APIGatewayRestResolver()

    @app.get("/", security=[{"apiKey": []}])
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema(
        security_schemes={
            "apiKey": APIKey(name="X-API-KEY", description="API Key", in_=APIKeyIn.header),
        },
    )

    security = schema.security
    assert security is None

    operation = schema.paths["/"].get
    security = operation.security
    assert security is not None

    assert len(security) == 1
    assert security[0] == {"apiKey": []}
