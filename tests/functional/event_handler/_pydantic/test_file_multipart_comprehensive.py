"""
Comprehensive tests for File parameter multipart parsing and validation.
"""

import base64
import json
from typing import Annotated

import pytest

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form


def make_multipart_event(boundary="----WebKitFormBoundary7MA4YWxkTrZu0gW", body_parts=None, is_base64=False):
    """Create a multipart/form-data request event for testing."""
    if body_parts is None:
        body_parts = []

    # Build multipart body
    body_lines = []
    for part in body_parts:
        body_lines.append(f"--{boundary}")
        body_lines.append(
            f'Content-Disposition: form-data; name="{part["name"]}"'
            + (f'; filename="{part["filename"]}"' if part.get("filename") else "")
        )
        if part.get("content_type"):
            body_lines.append(f"Content-Type: {part['content_type']}")
        body_lines.append("")  # Empty line before content
        body_lines.append(part["content"])
    body_lines.append(f"--{boundary}--")

    body = "\r\n".join(body_lines)

    if is_base64:
        body = base64.b64encode(body.encode("utf-8")).decode("ascii")

    return {
        "resource": "/upload",
        "path": "/upload",
        "httpMethod": "POST",
        "headers": {"content-type": f"multipart/form-data; boundary={boundary}"},
        "multiValueHeaders": {},
        "queryStringParameters": None,
        "multiValueQueryStringParameters": {},
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "path": "/stage/upload",
            "accountId": "123456789012",
            "resourceId": "abcdef",
            "stage": "test",
            "requestId": "test-request-id",
            "identity": {
                "sourceIp": "127.0.0.1",
                "userAgent": "Custom User Agent String",
            },
            "resourcePath": "/upload",
            "httpMethod": "POST",
            "apiId": "abcdefghij",
        },
        "body": body,
        "isBase64Encoded": is_base64,
    }


def test_file_upload_basic_parsing():
    """Test basic file upload parsing from multipart data."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File(description="File to upload")]):
        return {"file_size": len(file), "message": "File uploaded successfully"}

    # Create a simple file upload
    event = make_multipart_event(
        body_parts=[{"name": "file", "filename": "test.txt", "content_type": "text/plain", "content": "Hello, world!"}]
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200

    response_body = json.loads(response["body"])
    assert response_body["file_size"] == 13  # len("Hello, world!")
    assert "uploaded successfully" in response_body["message"]


def test_file_upload_with_form_data():
    """Test file upload combined with form fields."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_with_metadata(
        file: Annotated[bytes, File(description="File to upload")],
        title: Annotated[str, Form(description="File title")],
        description: Annotated[str, Form(description="File description")],
    ):
        return {"file_size": len(file), "title": title, "description": description}

    # Create multipart data with file and form fields
    event = make_multipart_event(
        body_parts=[
            {
                "name": "file",
                "filename": "document.pdf",
                "content_type": "application/pdf",
                "content": "PDF content here",
            },
            {"name": "title", "content": "Important Document"},
            {"name": "description", "content": "This is a test document upload"},
        ]
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200

    response_body = json.loads(response["body"])
    assert response_body["file_size"] == 16  # len("PDF content here")
    assert response_body["title"] == "Important Document"
    assert response_body["description"] == "This is a test document upload"


def test_webkit_boundary_parsing():
    """Test parsing of WebKit-style boundaries."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"status": "ok", "size": len(file)}

    # Use a typical WebKit boundary format
    webkit_boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    event = make_multipart_event(
        boundary=webkit_boundary,
        body_parts=[
            {"name": "file", "filename": "test.jpg", "content_type": "image/jpeg", "content": "fake image data"}
        ],
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200

    response_body = json.loads(response["body"])
    assert response_body["status"] == "ok"
    assert response_body["size"] == 15  # len("fake image data")


def test_base64_encoded_multipart():
    """Test parsing of base64-encoded multipart data (common in Lambda)."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"received": True, "size": len(file)}

    # Create base64-encoded multipart event
    event = make_multipart_event(
        body_parts=[{"name": "file", "filename": "encoded.txt", "content": "This content is base64 encoded"}],
        is_base64=True,
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200

    response_body = json.loads(response["body"])
    assert response_body["received"] is True
    assert response_body["size"] == 30  # len("This content is base64 encoded")


def test_multiple_files():
    """Test handling multiple file uploads."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_files(file1: Annotated[bytes, File(alias="file1")], file2: Annotated[bytes, File(alias="file2")]):
        return {"file1_size": len(file1), "file2_size": len(file2)}

    event = make_multipart_event(
        body_parts=[
            {"name": "file1", "filename": "first.txt", "content": "First file content"},
            {"name": "file2", "filename": "second.txt", "content": "Second file content is longer"},
        ]
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200

    response_body = json.loads(response["body"])
    assert response_body["file1_size"] == 18  # len("First file content")
    assert response_body["file2_size"] == 29  # len("Second file content is longer")


def test_missing_required_file():
    """Test error handling when required file is missing."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"status": "uploaded"}

    # Create multipart event without the required file
    event = make_multipart_event(body_parts=[{"name": "other_field", "content": "not a file"}])

    response = app.resolve(event, {})
    assert response["statusCode"] == 422

    response_body = json.loads(response["body"])
    assert response_body["statusCode"] == 422
    assert "detail" in response_body


def test_invalid_boundary():
    """Test error handling for invalid multipart boundary."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"status": "uploaded"}

    # Create event with malformed multipart data (no boundary)
    event = {
        "resource": "/upload",
        "path": "/upload",
        "httpMethod": "POST",
        "headers": {"content-type": "multipart/form-data"},  # Missing boundary
        "multiValueHeaders": {},
        "queryStringParameters": None,
        "multiValueQueryStringParameters": {},
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "path": "/stage/upload",
            "accountId": "123456789012",
            "resourceId": "abcdef",
            "stage": "test",
            "requestId": "test-request-id",
            "identity": {"sourceIp": "127.0.0.1"},
            "resourcePath": "/upload",
            "httpMethod": "POST",
            "apiId": "abcdefghij",
        },
        "body": "invalid multipart data",
        "isBase64Encoded": False,
    }

    response = app.resolve(event, {})
    assert response["statusCode"] == 422

    response_body = json.loads(response["body"])
    assert response_body["statusCode"] == 422
    assert "detail" in response_body


def test_file_with_constraints():
    """Test File parameter with validation constraints."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File(description="Small file", max_length=10)]):
        return {"status": "uploaded", "size": len(file)}

    # Test file that's too large
    event = make_multipart_event(
        body_parts=[
            {"name": "file", "filename": "large.txt", "content": "This file content is way too long for the constraint"}
        ]
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 422

    response_body = json.loads(response["body"])
    assert response_body["statusCode"] == 422
    assert "detail" in response_body


def test_optional_file_parameter():
    """Test optional File parameter handling."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(
        message: Annotated[str, Form(description="Required message")],
        file: Annotated[bytes | None, File(description="Optional file")] = None,
    ):
        return {"has_file": file is not None, "file_size": len(file) if file else 0, "message": message}

    # Test without file (only form data)
    event = make_multipart_event(body_parts=[{"name": "message", "content": "Upload without file"}])

    response = app.resolve(event, {})
    assert response["statusCode"] == 200

    response_body = json.loads(response["body"])
    assert response_body["has_file"] is False
    assert response_body["file_size"] == 0
    assert response_body["message"] == "Upload without file"


def test_empty_file_upload():
    """Test handling of empty file uploads."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(file: Annotated[bytes, File()]):
        return {"size": len(file), "is_empty": len(file) == 0}

    event = make_multipart_event(
        body_parts=[
            {
                "name": "file",
                "filename": "empty.txt",
                "content": "",  # Empty file
            }
        ]
    )

    response = app.resolve(event, {})
    assert response["statusCode"] == 200

    response_body = json.loads(response["body"])
    assert response_body["size"] == 0
    assert response_body["is_empty"] is True
