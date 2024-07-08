import json

from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver, Router
from aws_lambda_powertools.event_handler.openapi.models import (
    APIKey,
    APIKeyIn,
    OAuth2,
    OAuthFlowImplicit,
    OAuthFlows,
    Server,
)


def test_openapi_extension_root_level():
    app = APIGatewayRestResolver()

    cors_config = {
        "maxAge": 0,
        "allowCredentials": False,
    }

    schema = json.loads(
        app.get_openapi_json_schema(
            openapi_extensions={"x-amazon-apigateway-cors": cors_config},
        ),
    )

    assert "x-amazon-apigateway-cors" in schema
    assert schema["x-amazon-apigateway-cors"] == cors_config


def test_openapi_extension_server_level():
    app = APIGatewayRestResolver()

    endpoint_config = {
        "disableExecuteApiEndpoint": True,
        "vpcEndpointIds": ["vpce-0df8e77555fca0000"],
    }

    server_config = {
        "url": "https://example.org/",
        "description": "Example website",
    }

    schema = json.loads(
        app.get_openapi_json_schema(
            title="Hello API",
            version="1.0.0",
            servers=[
                Server(
                    **server_config,
                    openapi_extensions={
                        "x-amazon-apigateway-endpoint-configuration": endpoint_config,
                    },
                ),
            ],
        ),
    )

    assert "x-amazon-apigateway-endpoint-configuration" in schema["servers"][0]
    assert schema["servers"][0]["x-amazon-apigateway-endpoint-configuration"] == endpoint_config


def test_openapi_extension_security_scheme_level_with_api_key():
    app = APIGatewayRestResolver()

    authorizer_config = {
        "authorizerUri": "arn:aws:apigateway:us-east-1:...:function:authorizer/invocations",
        "authorizerResultTtlInSeconds": 300,
        "type": "token",
    }

    api_key_config = {
        "name": "X-API-KEY",
        "description": "API Key",
        "in_": APIKeyIn.header,
    }

    schema = json.loads(
        app.get_openapi_json_schema(
            security_schemes={
                "apiKey": APIKey(
                    **api_key_config,
                    openapi_extensions={
                        "x-amazon-apigateway-authtype": "custom",
                        "x-amazon-apigateway-authorizer": authorizer_config,
                    },
                ),
            },
        ),
    )

    assert "x-amazon-apigateway-authtype" in schema["components"]["securitySchemes"]["apiKey"]
    assert schema["components"]["securitySchemes"]["apiKey"]["x-amazon-apigateway-authtype"] == "custom"
    assert schema["components"]["securitySchemes"]["apiKey"]["x-amazon-apigateway-authorizer"] == authorizer_config


def test_openapi_extension_security_scheme_level_with_oauth2():
    app = APIGatewayRestResolver()

    authorizer_config = {
        "identitySource": "$request.header.Authorization",
        "jwtConfiguration": {
            "audience": ["test"],
            "issuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_xxxxx/",
        },
        "type": "jwt",
    }

    oauth2_config = {
        "flows": OAuthFlows(
            implicit=OAuthFlowImplicit(
                authorizationUrl="https://example.com/oauth2/authorize",
            ),
        ),
    }

    schema = json.loads(
        app.get_openapi_json_schema(
            security_schemes={
                "oauth2": OAuth2(
                    **oauth2_config,
                    openapi_extensions={
                        "x-amazon-apigateway-authorizer": authorizer_config,
                    },
                ),
            },
        ),
    )

    assert "x-amazon-apigateway-authorizer" in schema["components"]["securitySchemes"]["oauth2"]
    assert schema["components"]["securitySchemes"]["oauth2"]["x-amazon-apigateway-authorizer"] == authorizer_config


def test_openapi_extension_operation_level(openapi_extension_integration_detail):
    app = APIGatewayRestResolver()

    @app.get("/test", openapi_extensions={"x-amazon-apigateway-integration": openapi_extension_integration_detail})
    def lambda_handler():
        pass

    schema = json.loads(app.get_openapi_json_schema())

    assert "x-amazon-apigateway-integration" in schema["paths"]["/test"]["get"]
    assert schema["paths"]["/test"]["get"]["x-amazon-apigateway-integration"] == openapi_extension_integration_detail


def test_openapi_extension_operation_level_multiple_paths(
    openapi_extension_integration_detail,
    openapi_extension_validator_detail,
):
    app = APIGatewayRestResolver()

    @app.get("/test", openapi_extensions={"x-amazon-apigateway-integration": openapi_extension_integration_detail})
    def lambda_handler_get():
        pass

    @app.post("/test", openapi_extensions={"x-amazon-apigateway-request-validator": openapi_extension_validator_detail})
    def lambda_handler_post():
        pass

    schema = json.loads(app.get_openapi_json_schema())

    assert "x-amazon-apigateway-integration" in schema["paths"]["/test"]["get"]
    assert schema["paths"]["/test"]["get"]["x-amazon-apigateway-integration"] == openapi_extension_integration_detail

    assert "x-amazon-apigateway-integration" not in schema["paths"]["/test"]["post"]
    assert "x-amazon-apigateway-request-validator" in schema["paths"]["/test"]["post"]
    assert (
        schema["paths"]["/test"]["post"]["x-amazon-apigateway-request-validator"] == openapi_extension_validator_detail
    )


def test_openapi_extension_operation_level_with_router(openapi_extension_integration_detail):
    app = APIGatewayRestResolver()
    router = Router()

    @router.get("/test", openapi_extensions={"x-amazon-apigateway-integration": openapi_extension_integration_detail})
    def lambda_handler():
        pass

    app.include_router(router)

    schema = json.loads(app.get_openapi_json_schema())

    assert "x-amazon-apigateway-integration" in schema["paths"]["/test"]["get"]
    assert schema["paths"]["/test"]["get"]["x-amazon-apigateway-integration"] == openapi_extension_integration_detail


def test_openapi_extension_operation_level_multiple_paths_with_router(
    openapi_extension_integration_detail,
    openapi_extension_validator_detail,
):
    app = APIGatewayRestResolver()
    router = Router()

    @router.get("/test", openapi_extensions={"x-amazon-apigateway-integration": openapi_extension_integration_detail})
    def lambda_handler_get():
        pass

    @router.post(
        "/test",
        openapi_extensions={"x-amazon-apigateway-request-validator": openapi_extension_validator_detail},
    )
    def lambda_handler_post():
        pass

    app.include_router(router)

    schema = json.loads(app.get_openapi_json_schema())

    assert "x-amazon-apigateway-integration" in schema["paths"]["/test"]["get"]
    assert schema["paths"]["/test"]["get"]["x-amazon-apigateway-integration"] == openapi_extension_integration_detail

    assert "x-amazon-apigateway-integration" not in schema["paths"]["/test"]["post"]
    assert "x-amazon-apigateway-request-validator" in schema["paths"]["/test"]["post"]
    assert (
        schema["paths"]["/test"]["post"]["x-amazon-apigateway-request-validator"] == openapi_extension_validator_detail
    )
