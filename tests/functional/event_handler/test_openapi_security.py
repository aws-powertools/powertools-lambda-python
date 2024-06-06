import pytest

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.openapi.models import APIKey, APIKeyIn


def test_openapi_top_level_security():
    # GIVEN an APIGatewayRestResolver instance
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    # WHEN the get_openapi_schema method is called with a security scheme
    schema = app.get_openapi_schema(
        security_schemes={
            "apiKey": APIKey(name="X-API-KEY", description="API Key", in_=APIKeyIn.header),
        },
        security=[{"apiKey": []}],
    )

    # THEN the resulting schema should have security defined at the top level
    security = schema.security
    assert security is not None

    assert len(security) == 1
    assert security[0] == {"apiKey": []}


def test_openapi_top_level_security_missing():
    # GIVEN an APIGatewayRestResolver instance
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    # WHEN the get_openapi_schema method is called with security defined without security schemes
    # THEN a ValueError should be raised
    with pytest.raises(ValueError):
        app.get_openapi_schema(
            security=[{"apiKey": []}],
        )


def test_openapi_operation_security():
    # GIVEN an APIGatewayRestResolver instance
    app = APIGatewayRestResolver()

    @app.get("/", security=[{"apiKey": []}])
    def handler():
        raise NotImplementedError()

    # WHEN the get_openapi_schema method is called with security defined at the operation level
    schema = app.get_openapi_schema(
        security_schemes={
            "apiKey": APIKey(name="X-API-KEY", description="API Key", in_=APIKeyIn.header),
        },
    )

    # THEN the resulting schema should have security defined at the operation level, not the top level
    top_level_security = schema.security
    path_level_security = schema.paths["/"].get.security
    assert top_level_security is None
    assert path_level_security[0] == {"apiKey": []}


def test_openapi_operation_security_with_router():
    # GIVEN an APIGatewayRestResolver instance with a Router
    app = APIGatewayRestResolver()
    router = Router()

    @router.get("/", security=[{"apiKey": []}])
    def handler():
        raise NotImplementedError()

    app.include_router(router)

    # WHEN the get_openapi_schema method is called with security defined at the operation level in the Router
    schema = app.get_openapi_schema(
        security_schemes={
            "apiKey": APIKey(name="X-API-KEY", description="API Key", in_=APIKeyIn.header),
        },
    )

    # THEN the resulting schema should have security defined at the operation level
    top_level_security = schema.security
    path_level_security = schema.paths["/"].get.security
    assert top_level_security is None
    assert path_level_security[0] == {"apiKey": []}
