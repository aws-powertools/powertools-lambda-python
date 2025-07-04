from __future__ import annotations

from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.models import ExternalDocumentation


def test_openapi_schema_no_external_documentation():
    app = APIGatewayRestResolver()

    schema = app.get_openapi_schema(title="Hello API", version="1.0.0")
    assert not schema.externalDocs


def test_openapi_schema_external_documentation():
    app = APIGatewayRestResolver()

    schema = app.get_openapi_schema(
        title="Hello API",
        version="1.0.0",
        external_documentation=ExternalDocumentation(
            description="Find out more about this API",
            url="https://example.org/docs",
        ),
    )

    assert schema.externalDocs
    assert schema.externalDocs.description == "Find out more about this API"
    assert schema.externalDocs.url == "https://example.org/docs"
