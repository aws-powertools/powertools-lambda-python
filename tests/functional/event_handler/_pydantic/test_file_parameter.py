"""
Comprehensive tests for File parameter functionality in AWS Lambda Powertools Event Handler.

This module tests all aspects of File parameter handling including:
- Basic file upload functionality
- Multipart/form-data parsing
- WebKit browser compatibility
- Error handling and edge cases
- Validation constraints
- Mixed file and form data scenarios
"""
import base64
import json
from typing import Annotated

import pytest

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form


class TestFileParameterBasics:
    """Test basic File parameter functionality and integration."""

    def test_file_parameter_basic(self):
        """Test basic File parameter functionality."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"message": "File uploaded", "size": len(file)}

        # Create multipart form data
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="test.txt"',
            "Content-Type: text/plain",
            "",
            "Hello, World!",
            f"--{boundary}--",
        ]
        body = "\r\n".join(body_lines)

        event = {
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
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/upload",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": body,
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 200

        response_body = json.loads(response["body"])
        assert response_body["message"] == "File uploaded"
        assert response_body["size"] == 13  # "Hello, World!" is 13 bytes

    def test_form_parameter_validation(self):
        """Test that regular Form parameters work alongside File parameters."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_with_metadata(
            file: Annotated[bytes, File()],
            description: Annotated[str, Form()],
        ):
            return {
                "file_size": len(file),
                "description": description,
                "status": "uploaded",
            }

        # Create multipart form data with both file and form field
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="document.txt"',
            "Content-Type: text/plain",
            "",
            "File content here",
            f"--{boundary}",
            'Content-Disposition: form-data; name="description"',
            "",
            "This is a test document",
            f"--{boundary}--",
        ]
        body = "\r\n".join(body_lines)

        event = {
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
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/upload",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": body,
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 200

        response_body = json.loads(response["body"])
        assert response_body["file_size"] == 17  # "File content here" is 17 bytes
        assert response_body["description"] == "This is a test document"
        assert response_body["status"] == "uploaded"


class TestMultipartParsing:
    """Test multipart/form-data parsing functionality."""

    def test_webkit_boundary_parsing(self):
        """Test WebKit-style boundary parsing (Safari/Chrome compatibility)."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        # Use WebKit boundary format
        webkit_boundary = "WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{webkit_boundary}",
            'Content-Disposition: form-data; name="file"; filename="test.txt"',
            "Content-Type: text/plain",
            "",
            "WebKit test content",
            f"--{webkit_boundary}--",
        ]
        body = "\r\n".join(body_lines)

        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; boundary={webkit_boundary}"},
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
            "body": body,
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 200

        response_body = json.loads(response["body"])
        assert response_body["size"] == 19  # "WebKit test content" is 19 bytes

    def test_base64_encoded_multipart(self):
        """Test parsing of base64-encoded multipart data."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        # Create multipart content and encode as base64
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="encoded.txt"',
            "Content-Type: text/plain",
            "",
            "Base64 encoded content",
            f"--{boundary}--",
        ]
        multipart_body = "\r\n".join(body_lines)
        encoded_body = base64.b64encode(multipart_body.encode("utf-8")).decode("ascii")

        event = {
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
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/upload",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": encoded_body,
            "isBase64Encoded": True,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 200

        response_body = json.loads(response["body"])
        assert response_body["size"] == 22  # "Base64 encoded content" is 22 bytes

    def test_multiple_files(self):
        """Test handling multiple file uploads in a single request."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_files(
            file1: Annotated[bytes, File()],
            file2: Annotated[bytes, File()],
        ):
            return {
                "status": "uploaded",
                "file1_size": len(file1),
                "file2_size": len(file2),
            }

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file1"; filename="first.txt"',
            "Content-Type: text/plain",
            "",
            "First file content",
            f"--{boundary}",
            'Content-Disposition: form-data; name="file2"; filename="second.txt"',
            "Content-Type: text/plain",
            "",
            "Second file content",
            f"--{boundary}--",
        ]
        body = "\r\n".join(body_lines)

        event = {
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
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/upload",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": body,
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 200

        response_body = json.loads(response["body"])
        assert response_body["file1_size"] == 18  # "First file content" is 18 bytes
        assert response_body["file2_size"] == 19  # "Second file content" is 19 bytes


class TestValidationAndConstraints:
    """Test File parameter validation and constraints."""

    def test_missing_required_file(self):
        """Test validation error when required file is missing."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        # Send request without file data
        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": "multipart/form-data; boundary=test"},
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
            "body": "--test\r\nContent-Disposition: form-data; name=\"other\"\r\n\r\nvalue\r\n--test--",
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 422  # Validation error

    def test_optional_file_parameter(self):
        """Test handling of optional File parameters."""
        from typing import Union

        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[Union[bytes, None], File()] = None):
            if file is None:
                return {"status": "no file uploaded", "size": 0, "is_empty": True}
            return {"status": "file uploaded", "size": len(file), "is_empty": False}

        # Send request without file
        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": "multipart/form-data; boundary=test"},
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
            "body": "--test\r\nContent-Disposition: form-data; name=\"other\"\r\n\r\nvalue\r\n--test--",
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 200

        response_body = json.loads(response["body"])
        assert response_body["status"] == "no file uploaded"
        assert response_body["is_empty"] is True

    def test_empty_file_upload(self):
        """Test handling of empty file uploads."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file), "is_empty": len(file) == 0}

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="empty.txt"',
            "Content-Type: text/plain",
            "",
            "",  # Empty file content
            f"--{boundary}--",
        ]
        body = "\r\n".join(body_lines)

        event = {
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
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/upload",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": body,
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 200

        response_body = json.loads(response["body"])
        assert response_body["size"] == 0
        assert response_body["is_empty"] is True


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_boundary(self):
        """Test handling of invalid or missing boundary."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        # Missing boundary in content-type
        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": "multipart/form-data"},  # No boundary
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
            "body": "some data",
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 422  # Should fail validation

    def test_malformed_multipart_data(self):
        """Test handling of malformed multipart data."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        # Malformed multipart without proper headers
        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": "multipart/form-data; boundary=test"},
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
            "body": "malformed data without proper multipart structure",
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 422  # Should fail validation

    def test_base64_decode_failure(self):
        """Test handling of malformed base64 encoded content."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"},
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
            "body": "invalid-base64-content!@#$",
            "isBase64Encoded": True,
        }

        response = app.resolve(event, {})
        # Should handle the decode failure gracefully and parse as text
        assert response["statusCode"] == 422  # Will fail validation but shouldn't crash

    def test_empty_body_edge_cases(self):
        """Test various empty body scenarios."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        # Test None body
        event_none = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": "multipart/form-data; boundary=test"},
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
            "body": None,
            "isBase64Encoded": False,
        }

        response = app.resolve(event_none, {})
        assert response["statusCode"] == 422

        # Test empty string body
        event_empty = {**event_none, "body": ""}
        response = app.resolve(event_empty, {})
        assert response["statusCode"] == 422

    def test_unicode_decode_errors(self):
        """Test handling of content that can't be decoded as UTF-8."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_with_data(
            file: Annotated[bytes, File()],
            metadata: Annotated[str, Form()],
        ):
            return {"status": "uploaded", "metadata_type": type(metadata).__name__}

        # Create multipart data with invalid UTF-8 in form field
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        invalid_utf8_bytes = b"\xff\xfe\xfd"
        
        body_parts = []
        body_parts.append(f"--{boundary}")
        body_parts.append('Content-Disposition: form-data; name="file"; filename="test.txt"')
        body_parts.append("Content-Type: text/plain")
        body_parts.append("")
        body_parts.append("File content")
        
        body_parts.append(f"--{boundary}")
        body_parts.append('Content-Disposition: form-data; name="metadata"')
        body_parts.append("")
        
        body_start = "\r\n".join(body_parts) + "\r\n"
        body_end = f"\r\n--{boundary}--"
        
        # Combine with the invalid UTF-8 bytes
        full_body = body_start.encode("utf-8") + invalid_utf8_bytes + body_end.encode("utf-8")

        event = {
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
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/upload",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": base64.b64encode(full_body).decode("ascii"),
            "isBase64Encoded": True,
        }

        response = app.resolve(event, {})
        # Should handle the Unicode decode error gracefully
        assert response["statusCode"] in [200, 422]


class TestBoundaryExtraction:
    """Test boundary extraction from various content-type formats."""

    def test_webkit_boundary_extraction(self):
        """Test extraction of WebKit-style boundaries."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        webkit_boundary = "WebKitFormBoundary7MA4YWxkTrZu0gW123"
        
        body_lines = [
            f"--{webkit_boundary}",
            'Content-Disposition: form-data; name="file"; filename="test.txt"',
            "Content-Type: text/plain",
            "",
            "Test content",
            f"--{webkit_boundary}--",
        ]
        multipart_body = "\r\n".join(body_lines)

        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; boundary={webkit_boundary}"},
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
            "body": multipart_body,
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 200

    def test_quoted_boundary_extraction(self):
        """Test extraction of quoted boundaries."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        boundary = "test-boundary-123"
        
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="test.txt"',
            "Content-Type: text/plain",
            "",
            "Test content",
            f"--{boundary}--",
        ]
        multipart_body = "\r\n".join(body_lines)

        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": f'multipart/form-data; boundary="{boundary}"'},  # Quoted
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
            "body": multipart_body,
            "isBase64Encoded": False,
        }

        response = app.resolve(event, {})
        assert response["statusCode"] == 200
