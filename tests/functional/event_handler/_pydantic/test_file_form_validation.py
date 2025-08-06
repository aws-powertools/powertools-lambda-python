"""
Test File and Form parameter validation functionality.
"""

import json
from typing import Annotated

import pytest

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form


def make_request_event(method="GET", path="/", body="", headers=None, query_params=None):
    """Create a minimal API Gateway request event for testing."""
    return {
        "resource": path,
        "path": path,
        "httpMethod": method,
        "headers": headers or {},
        "multiValueHeaders": {},
        "queryStringParameters": query_params,
        "multiValueQueryStringParameters": {},
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "path": f"/stage{path}",
            "accountId": "123456789012",
            "resourceId": "abcdef",
            "stage": "test",
            "requestId": "test-request-id",
            "identity": {
                "cognitoIdentityPoolId": None,
                "accountId": None,
                "cognitoIdentityId": None,
                "caller": None,
                "apiKey": None,
                "sourceIp": "127.0.0.1",
                "cognitoAuthenticationType": None,
                "cognitoAuthenticationProvider": None,
                "userArn": None,
                "userAgent": "Custom User Agent String",
                "user": None,
            },
            "resourcePath": path,
            "httpMethod": method,
            "apiId": "abcdefghij",
        },
        "body": body,
        "isBase64Encoded": False,
    }


def test_form_parameter_validation():
    """Test basic form parameter validation."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/contact")
    def contact_form(
        name: Annotated[str, Form(description="Contact name")], email: Annotated[str, Form(description="Contact email")]
    ):
        return {"message": f"Hello {name}, we'll contact you at {email}"}

    # Create form data request
    body = "name=John+Doe&email=john%40example.com"

    event = make_request_event(
        method="POST", path="/contact", body=body, headers={"content-type": "application/x-www-form-urlencoded"}
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200

    response_body = json.loads(response["body"])
    assert "John Doe" in response_body["message"]
    assert "john@example.com" in response_body["message"]


def test_file_parameter_basic():
    """Test that File parameters are properly recognized (basic functionality)."""
    app = APIGatewayRestResolver()

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File(description="File to upload")]):
        return {"message": "File parameter recognized"}

    # Test that the schema is generated correctly
    schema = app.get_openapi_schema()
    upload_op = schema.paths["/upload"].post

    assert "multipart/form-data" in upload_op.requestBody.content

    # Get the actual schema from components
    multipart_content = upload_op.requestBody.content["multipart/form-data"]
    ref_name = multipart_content.schema_.ref.split("/")[-1]
    actual_schema = schema.components.schemas[ref_name]

    assert "file" in actual_schema.properties
    assert actual_schema.properties["file"].format == "binary"


def test_mixed_file_and_form_schema():
    """Test that mixed File and Form parameters generate correct schema."""
    app = APIGatewayRestResolver()

    @app.post("/upload")
    def upload_with_metadata(
        file: Annotated[bytes, File(description="File to upload")],
        title: Annotated[str, Form(description="File title")],
    ):
        return {"message": "Mixed parameters recognized"}

    # Test that the schema is generated correctly
    schema = app.get_openapi_schema()
    upload_op = schema.paths["/upload"].post

    # Should use multipart/form-data when File parameters are present
    assert "multipart/form-data" in upload_op.requestBody.content

    # Get the actual schema from components
    multipart_content = upload_op.requestBody.content["multipart/form-data"]
    ref_name = multipart_content.schema_.ref.split("/")[-1]
    actual_schema = schema.components.schemas[ref_name]

    # Should have both file and form fields
    assert "file" in actual_schema.properties
    assert "title" in actual_schema.properties
    assert actual_schema.properties["file"].format == "binary"
    assert actual_schema.properties["title"].type == "string"
