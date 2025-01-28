from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.models import (
    APIKey,
    APIKeyIn,
    HTTPBearer,
    MutualTLS,
    OAuth2,
    OAuthFlowImplicit,
    OAuthFlows,
    OpenIdConnect,
)


def test_openapi_security_scheme_api_key():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema(
        security_schemes={
            "apiKey": APIKey(name="X-API-KEY", description="API Key", in_=APIKeyIn.header),
        },
    )

    security_schemes = schema.components.securitySchemes
    assert security_schemes is not None

    assert "apiKey" in security_schemes
    api_key_scheme = security_schemes["apiKey"]
    assert api_key_scheme.type_.value == "apiKey"
    assert api_key_scheme.name == "X-API-KEY"
    assert api_key_scheme.description == "API Key"
    assert api_key_scheme.in_.value == "header"


def test_openapi_security_scheme_http():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema(
        security_schemes={
            "bearerAuth": HTTPBearer(
                description="JWT Token",
                bearerFormat="JWT",
            ),
        },
    )

    security_schemes = schema.components.securitySchemes
    assert security_schemes is not None

    assert "bearerAuth" in security_schemes
    http_scheme = security_schemes["bearerAuth"]
    assert http_scheme.type_.value == "http"
    assert http_scheme.scheme == "bearer"
    assert http_scheme.bearerFormat == "JWT"


def test_openapi_security_scheme_oauth2():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema(
        security_schemes={
            "oauth2": OAuth2(
                flows=OAuthFlows(
                    implicit=OAuthFlowImplicit(
                        authorizationUrl="https://example.com/oauth2/authorize",
                    ),
                ),
            ),
        },
    )

    security_schemes = schema.components.securitySchemes
    assert security_schemes is not None

    assert "oauth2" in security_schemes
    oauth2_scheme = security_schemes["oauth2"]
    assert oauth2_scheme.type_.value == "oauth2"
    assert oauth2_scheme.flows.implicit.authorizationUrl == "https://example.com/oauth2/authorize"


def test_openapi_security_scheme_open_id_connect():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema(
        security_schemes={
            "openIdConnect": OpenIdConnect(
                openIdConnectUrl="https://example.com/oauth2/authorize",
            ),
        },
    )

    security_schemes = schema.components.securitySchemes
    assert security_schemes is not None

    assert "openIdConnect" in security_schemes
    open_id_connect_scheme = security_schemes["openIdConnect"]
    assert open_id_connect_scheme.type_.value == "openIdConnect"
    assert open_id_connect_scheme.openIdConnectUrl == "https://example.com/oauth2/authorize"


def test_openapi_security_scheme_mtls():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema(
        security_schemes={
            "mutualTLS": MutualTLS(description="mTLS Authentication"),
        },
    )

    security_schemes = schema.components.securitySchemes
    assert security_schemes is not None

    assert "mutualTLS" in security_schemes
    mtls_scheme = security_schemes["mutualTLS"]
    assert mtls_scheme.description == "mTLS Authentication"
