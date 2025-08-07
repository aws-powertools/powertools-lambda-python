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

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form, UploadFile


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
            "body": '--test\r\nContent-Disposition: form-data; name="other"\r\n\r\nvalue\r\n--test--',
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
            "body": '--test\r\nContent-Disposition: form-data; name="other"\r\n\r\nvalue\r\n--test--',
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


class TestFileParameterEdgeCases:
    """Test additional edge cases for comprehensive coverage."""

    def test_body_none_handling(self):
        """Test when event body is None."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

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
            "body": None,  # Explicitly set to None
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 422  # Missing required file

    def test_no_boundary_in_content_type(self):
        """Test when no boundary is provided in Content-Type."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

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
            "body": "some content",
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 422  # Validation error for missing boundary

    def test_lf_only_line_endings(self):
        """Test parsing with LF-only line endings instead of CRLF."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        boundary = "test-boundary"
        # Use LF (\n) instead of CRLF (\r\n)
        multipart_data = (
            f"--{boundary}\n"
            'Content-Disposition: form-data; name="file"; filename="test.txt"\n'
            "Content-Type: text/plain\n"
            "\n"
            "test content with LF\n"
            f"--{boundary}--"
        )

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
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["size"] == 20  # "test content with LF"

    def test_unsupported_content_type_handling(self):
        """Test handling of unsupported content types."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": "application/xml"},  # Unsupported content type
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
            "body": "some content",
            "isBase64Encoded": False,
        }

        try:
            app(event, {})
            raise AssertionError("Should have raised NotImplementedError")
        except NotImplementedError as e:
            assert "application/xml" in str(e)


class TestCoverageSpecificScenarios:
    """Additional tests to improve code coverage for specific edge cases."""

    def test_base64_decode_exception_handling(self):
        """Test base64 decode exception handling."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        # Invalid base64 that will trigger exception
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
            "body": "invalid===base64==data",
            "isBase64Encoded": True,  # This will trigger base64 decode attempt and exception
        }

        result = app(event, {})
        assert result["statusCode"] == 422

    def test_webkit_boundary_pattern_coverage(self):
        """Test WebKit boundary pattern matching and fallback."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        # Test with WebKit boundary pattern
        webkit_boundary = "WebKitFormBoundary" + "abcd1234567890"
        multipart_data = (
            f"--{webkit_boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "webkit content\r\n"
            f"--{webkit_boundary}--"
        )

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
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200

    def test_malformed_section_parsing(self):
        """Test parsing of malformed sections without proper headers."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        boundary = "test-boundary"
        # Create section without proper name attribute
        malformed_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; filename="test.txt"\r\n'  # No name attribute
            "Content-Type: text/plain\r\n"
            "\r\n"
            "content without name\r\n"
            f"--{boundary}--"
        )

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
            "body": malformed_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 422  # Should handle gracefully

    def test_empty_section_handling(self):
        """Test handling of empty sections in multipart data."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded"}

        boundary = "test-boundary"
        # Include empty sections that should be skipped
        multipart_data = (
            f"--{boundary}\r\n"
            "\r\n"  # Empty section
            f"\r\n--{boundary}\r\n"
            "\r\n"  # Another empty section
            f"\r\n--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "actual content\r\n"
            f"--{boundary}--"
        )

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
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200

    def test_unicode_decode_error_handling(self):
        """Test unicode decode error handling in form field processing."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()], text: Annotated[str, Form()]):
            return {"status": "uploaded", "text": text}

        boundary = "test-boundary"
        # Include non-UTF8 bytes that will cause decode issues
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="text"\r\n'
            "\r\n"
            "text with unicode \xff\xfe issues\r\n"  # Invalid UTF-8 sequence
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "file content\r\n"
            f"--{boundary}--"
        )

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
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200
        # Should handle decode errors gracefully with replacement characters

    def test_json_decode_error_coverage(self):
        """Test JSON decode error handling."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/data")
        def process_data(data: dict):
            return {"received": data}

        event = {
            "resource": "/data",
            "path": "/data",
            "httpMethod": "POST",
            "headers": {"content-type": "application/json"},
            "multiValueHeaders": {},
            "queryStringParameters": None,
            "multiValueQueryStringParameters": {},
            "pathParameters": None,
            "stageVariables": None,
            "requestContext": {
                "path": "/stage/data",
                "accountId": "123456789012",
                "resourceId": "abcdef",
                "stage": "test",
                "requestId": "test-request-id",
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/data",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": "invalid json {",  # Invalid JSON
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 422  # JSON validation error


class TestMissingCoverageLines:
    """Target specific missing coverage lines identified by Codecov."""

    def test_multipart_boundary_without_quotes(self):
        """Test boundary extraction without quotes - targets specific parsing lines."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        boundary = "simple-boundary-123"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "unquoted boundary content\r\n"
            f"--{boundary}--"
        )

        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; boundary={boundary}"},  # No quotes
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
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["size"] == 25  # "unquoted boundary content"

    def test_multipart_form_data_with_charset(self):
        """Test multipart parsing with charset parameter in content type."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        boundary = "charset-boundary"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "content with charset\r\n"
            f"--{boundary}--"
        )

        event = {
            "resource": "/upload",
            "path": "/upload",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; charset=utf-8; boundary={boundary}"},
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
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200

    def test_file_parameter_json_schema_generation(self):
        """Test File parameter JSON schema generation - targets params.py lines."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File(description="A test file", title="TestFile")]):
            return {"status": "uploaded", "size": len(file)}

        boundary = "schema-boundary"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="schema_test.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "schema test content\r\n"
            f"--{boundary}--"
        )

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
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200

    def test_has_file_params_dependency_resolution(self):
        """Test dependency resolution with file parameters - targets dependant.py lines."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/mixed")
        def upload_mixed(
            file: Annotated[bytes, File()],
            form_field: Annotated[str, Form()],
            regular_param: str = "default",
        ):
            return {"file_size": len(file), "form_field": form_field, "regular_param": regular_param}

        boundary = "dependency-boundary"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="form_field"\r\n'
            "\r\n"
            "form data value\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="dep_test.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "dependency test\r\n"
            f"--{boundary}--"
        )

        event = {
            "resource": "/mixed",
            "path": "/mixed",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; boundary={boundary}"},
            "multiValueHeaders": {},
            "queryStringParameters": {"regular_param": "query_value"},
            "multiValueQueryStringParameters": {},
            "pathParameters": None,
            "stageVariables": None,
            "requestContext": {
                "path": "/stage/mixed",
                "accountId": "123456789012",
                "resourceId": "abcdef",
                "stage": "test",
                "requestId": "test-request-id",
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/mixed",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["file_size"] == 15  # "dependency test"
        assert response_data["form_field"] == "form data value"

    def test_content_disposition_header_edge_cases(self):
        """Test Content-Disposition header parsing edge cases."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        boundary = "header-edge-boundary"
        # Test with unusual but valid Content-Disposition format
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="edge.txt"; size=100\r\n'
            "Content-Type: application/octet-stream\r\n"
            "\r\n"
            "edge case content\r\n"
            f"--{boundary}--"
        )

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
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200

    def test_form_urlencoded_body_handling(self):
        """Test application/x-www-form-urlencoded content type handling."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/form")
        def process_form(name: Annotated[str, Form()], age: Annotated[int, Form()]):
            return {"name": name, "age": age}

        event = {
            "resource": "/form",
            "path": "/form",
            "httpMethod": "POST",
            "headers": {"content-type": "application/x-www-form-urlencoded"},
            "multiValueHeaders": {},
            "queryStringParameters": None,
            "multiValueQueryStringParameters": {},
            "pathParameters": None,
            "stageVariables": None,
            "requestContext": {
                "path": "/stage/form",
                "accountId": "123456789012",
                "resourceId": "abcdef",
                "stage": "test",
                "requestId": "test-request-id",
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/form",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": "name=John&age=30",
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["name"] == "John"
        assert response_data["age"] == 30

    def test_multipart_without_content_type_header(self):
        """Test multipart section without Content-Type header."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        boundary = "no-content-type-boundary"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="no_ctype.txt"\r\n'
            # No Content-Type header
            "\r\n"
            "no content type header\r\n"
            f"--{boundary}--"
        )

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
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200

    def test_base64_decode_with_padding_issues(self):
        """Test base64 decode with padding and encoding issues."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        boundary = "base64-padding-boundary"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="b64.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "base64 padding test\r\n"
            f"--{boundary}--"
        )

        # Create base64 with potential padding issues
        encoded_body = base64.b64encode(multipart_data.encode("utf-8")).decode("ascii")
        # Remove some padding to test the decode error handling
        encoded_body = encoded_body.rstrip("=")

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

        result = app(event, {})
        # Should handle gracefully - either succeed or return validation error
        assert result["statusCode"] in [200, 422]

    def test_complex_multipart_structure(self):
        """Test complex multipart structure with multiple field types."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/complex")
        def complex_upload(
            doc: Annotated[bytes, File()],
            image: Annotated[bytes, File()],
            title: Annotated[str, Form()],
            description: Annotated[str, Form()],
        ):
            return {"doc_size": len(doc), "image_size": len(image), "title": title, "description": description}

        boundary = "complex-multipart-boundary"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="title"\r\n'
            "\r\n"
            "Complex Document\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="doc"; filename="document.pdf"\r\n'
            "Content-Type: application/pdf\r\n"
            "\r\n"
            "PDF document content here\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="description"\r\n'
            "\r\n"
            "This is a complex multipart upload with multiple files and form fields\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="image"; filename="picture.jpg"\r\n'
            "Content-Type: image/jpeg\r\n"
            "\r\n"
            "JPEG image binary data\r\n"
            f"--{boundary}--"
        )

        event = {
            "resource": "/complex",
            "path": "/complex",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; boundary={boundary}"},
            "multiValueHeaders": {},
            "queryStringParameters": None,
            "multiValueQueryStringParameters": {},
            "pathParameters": None,
            "stageVariables": None,
            "requestContext": {
                "path": "/stage/complex",
                "accountId": "123456789012",
                "resourceId": "abcdef",
                "stage": "test",
                "requestId": "test-request-id",
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/complex",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["title"] == "Complex Document"
        assert response_data["doc_size"] == 25  # "PDF document content here"
        assert response_data["image_size"] == 22  # "JPEG image binary data"


class TestAdditionalCoverageTargets:
    """Target remaining specific missing coverage lines."""

    def test_file_validation_error_paths(self):
        """Test File parameter validation error paths."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/strict")
        def strict_upload(file: Annotated[bytes, File(min_length=100)]):
            return {"status": "uploaded", "size": len(file)}

        boundary = "validation-boundary"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="small.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "small\r\n"  # Too small for min_length=100
            f"--{boundary}--"
        )

        event = {
            "resource": "/strict",
            "path": "/strict",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; boundary={boundary}"},
            "multiValueHeaders": {},
            "queryStringParameters": None,
            "multiValueQueryStringParameters": {},
            "pathParameters": None,
            "stageVariables": None,
            "requestContext": {
                "path": "/stage/strict",
                "accountId": "123456789012",
                "resourceId": "abcdef",
                "stage": "test",
                "requestId": "test-request-id",
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/strict",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 422  # Validation error for length

    def test_multipart_section_header_parsing_edge_cases(self):
        """Test multipart section header parsing with various edge cases."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/header-test")
        def header_test(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        boundary = "header-test-boundary"
        # Test with extra whitespace and different header formats
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition:  form-data ; name="file" ; filename="spaced.txt" \r\n'  # Extra spaces
            "Content-Type:  text/plain  \r\n"  # Extra spaces
            "\r\n"
            "header parsing test\r\n"
            f"--{boundary}--"
        )

        event = {
            "resource": "/header-test",
            "path": "/header-test",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; boundary={boundary}"},
            "multiValueHeaders": {},
            "queryStringParameters": None,
            "multiValueQueryStringParameters": {},
            "pathParameters": None,
            "stageVariables": None,
            "requestContext": {
                "path": "/stage/header-test",
                "accountId": "123456789012",
                "resourceId": "abcdef",
                "stage": "test",
                "requestId": "test-request-id",
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/header-test",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200

    def test_dependency_injection_with_file_params(self):
        """Test dependency injection patterns with File parameters."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/dep-test")
        def dep_test(file: Annotated[bytes, File()], metadata: Annotated[str, Form()] = "default"):
            return {"file_size": len(file), "metadata": metadata}

        boundary = "dep-test-boundary"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="dep.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "dependency test\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="metadata"\r\n'
            "\r\n"
            "test metadata\r\n"
            f"--{boundary}--"
        )

        event = {
            "resource": "/dep-test",
            "path": "/dep-test",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; boundary={boundary}"},
            "multiValueHeaders": {},
            "queryStringParameters": None,
            "multiValueQueryStringParameters": {},
            "pathParameters": None,
            "stageVariables": None,
            "requestContext": {
                "path": "/stage/dep-test",
                "accountId": "123456789012",
                "resourceId": "abcdef",
                "stage": "test",
                "requestId": "test-request-id",
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/dep-test",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["metadata"] == "test metadata"

    def test_boundary_extraction_with_special_characters(self):
        """Test boundary extraction with special characters."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/special")
        def special_boundary(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        # Use boundary with special characters
        boundary = "special-chars_123.456+789"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="special.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "special boundary chars\r\n"
            f"--{boundary}--"
        )

        event = {
            "resource": "/special",
            "path": "/special",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; boundary={boundary}"},
            "multiValueHeaders": {},
            "queryStringParameters": None,
            "multiValueQueryStringParameters": {},
            "pathParameters": None,
            "stageVariables": None,
            "requestContext": {
                "path": "/stage/special",
                "accountId": "123456789012",
                "resourceId": "abcdef",
                "stage": "test",
                "requestId": "test-request-id",
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/special",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200

    def test_empty_multipart_sections_mixed_with_valid(self):
        """Test multipart with empty sections mixed with valid ones."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/mixed-empty")
        def mixed_empty(file: Annotated[bytes, File()]):
            return {"status": "uploaded", "size": len(file)}

        boundary = "mixed-empty-boundary"
        multipart_data = (
            f"--{boundary}\r\n"
            "\r\n"  # Empty section 1
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="invalid"\r\n'  # Section without proper content
            f"--{boundary}\r\n"
            "\r\n"  # Empty section 2
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="valid.txt"\r\n'
            "Content-Type: text/plain\r\n"
            "\r\n"
            "valid content\r\n"
            f"--{boundary}--"
        )

        event = {
            "resource": "/mixed-empty",
            "path": "/mixed-empty",
            "httpMethod": "POST",
            "headers": {"content-type": f"multipart/form-data; boundary={boundary}"},
            "multiValueHeaders": {},
            "queryStringParameters": None,
            "multiValueQueryStringParameters": {},
            "pathParameters": None,
            "stageVariables": None,
            "requestContext": {
                "path": "/stage/mixed-empty",
                "accountId": "123456789012",
                "resourceId": "abcdef",
                "stage": "test",
                "requestId": "test-request-id",
                "identity": {"sourceIp": "127.0.0.1"},
                "resourcePath": "/mixed-empty",
                "httpMethod": "POST",
                "apiId": "abcdefghij",
            },
            "body": multipart_data,
            "isBase64Encoded": False,
        }

        result = app(event, {})
        assert result["statusCode"] == 200


class TestUploadFileFeature:
    """Test the new UploadFile class functionality and metadata access."""

    def test_upload_file_with_metadata(self):
        """Test UploadFile provides access to filename, content_type, and metadata."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[UploadFile, File()]):
            return {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size,
                "content_preview": file.read(50).decode("utf-8", errors="ignore"),
                "has_headers": len(file.headers) > 0,
            }

        # Create multipart form data with detailed headers
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="test.txt"',
            "Content-Type: text/plain; charset=utf-8",
            "X-Custom-Header: custom-value",
            "",
            "Hello, World! This is a test file with metadata.",
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
        assert response_body["filename"] == "test.txt"
        assert response_body["content_type"] == "text/plain; charset=utf-8"
        assert response_body["size"] == 48  # Length of the test content
        assert response_body["content_preview"] == "Hello, World! This is a test file with metadata."
        assert response_body["has_headers"] is True

    def test_upload_file_backward_compatibility_with_bytes(self):
        """Test that existing code using bytes still works when using UploadFile."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[bytes, File()]):
            # Should receive bytes even when UploadFile is created internally
            return {"message": "File uploaded", "size": len(file), "type": type(file).__name__}

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="test.txt"',
            "Content-Type: text/plain",
            "",
            "Backward compatibility test",
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
        assert response_body["size"] == 27  # "Backward compatibility test"
        assert response_body["type"] == "bytes"  # Should receive bytes, not UploadFile

    def test_upload_file_mixed_with_form_data(self):
        """Test UploadFile works with regular form fields."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_with_metadata(
            file: Annotated[UploadFile, File()],
            description: Annotated[str, Form()],
            category: Annotated[str, Form()],
        ):
            return {
                "filename": file.filename,
                "file_size": file.size,
                "description": description,
                "category": category,
                "content_type": file.content_type,
            }

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="description"',
            "",
            "Test document",
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="document.pdf"',
            "Content-Type: application/pdf",
            "",
            "PDF content here",
            f"--{boundary}",
            'Content-Disposition: form-data; name="category"',
            "",
            "documents",
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
        assert response_body["filename"] == "document.pdf"
        assert response_body["file_size"] == 16  # "PDF content here"
        assert response_body["description"] == "Test document"
        assert response_body["category"] == "documents"
        assert response_body["content_type"] == "application/pdf"

    def test_upload_file_headers_access(self):
        """Test UploadFile provides access to all multipart headers."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[UploadFile, File()]):
            return {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size,
                "custom_header": file.headers.get("X-Upload-ID"),
                "file_hash": file.headers.get("X-File-Hash"),
                "all_headers": file.headers,
            }

        # Create multipart form data with custom headers
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="important-document.pdf"',
            "Content-Type: application/pdf",
            "X-Upload-ID: 12345",
            "X-File-Hash: abc123def456",
            "X-File-Version: 1.0",
            "",
            "PDF file content with metadata for reconstruction...",
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
        assert response_body["filename"] == "important-document.pdf"
        assert response_body["content_type"] == "application/pdf"
        assert response_body["size"] == 52  # Length of the content
        assert response_body["custom_header"] == "12345"
        assert response_body["file_hash"] == "abc123def456"
        assert "X-File-Version" in response_body["all_headers"]
        assert response_body["all_headers"]["X-File-Version"] == "1.0"

    def test_upload_file_read_method_functionality(self):
        """Test UploadFile read method for flexible content access."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def upload_file(file: Annotated[UploadFile, File()]):
            # Test different read patterns
            full_content = file.read()
            partial_content = file.read(20)
            return {
                "filename": file.filename,
                "full_size": len(full_content),
                "partial_size": len(partial_content),
                "partial_content": partial_content.decode("utf-8", errors="ignore"),
                "full_matches_file_property": full_content == file.file,
                "can_reconstruct": True,
            }

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="read_test.txt"',
            "Content-Type: text/plain",
            "",
            "This is a longer test content for read method testing and file reconstruction.",
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
        assert response_body["filename"] == "read_test.txt"
        assert response_body["full_size"] == 78  # Full content length
        assert response_body["partial_size"] == 20  # Partial read
        assert response_body["partial_content"] == "This is a longer tes"
        assert response_body["full_matches_file_property"] is True
        assert response_body["can_reconstruct"] is True

    def test_upload_file_reconstruction_scenario(self):
        """Test real-world file reconstruction scenario with UploadFile."""
        app = APIGatewayRestResolver(enable_validation=True)

        @app.post("/upload")
        def process_upload(file: Annotated[UploadFile, File()]):
            # Simulate file reconstruction for storage/processing
            reconstructed_file = {
                "original_filename": file.filename,
                "mime_type": file.content_type,
                "file_size_bytes": file.size,
                "file_content": file.file,  # Raw bytes for storage
                "metadata": file.headers,
                "can_save_to_s3": True,
                "can_process": file.content_type in ["text/plain", "application/pdf", "image/jpeg"],
            }

            return {
                "upload_id": "12345",
                "filename": reconstructed_file["original_filename"],
                "content_type": reconstructed_file["mime_type"],
                "size": reconstructed_file["file_size_bytes"],
                "processable": reconstructed_file["can_process"],
                "has_metadata": len(reconstructed_file["metadata"]) > 0,
                "ready_for_storage": reconstructed_file["can_save_to_s3"],
            }

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="file"; filename="user-document.pdf"',
            "Content-Type: application/pdf",
            "X-Original-Size: 1024",
            "X-Upload-Source: web-app",
            "",
            "Binary PDF content that would be stored in S3...",
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
        assert response_body["upload_id"] == "12345"
        assert response_body["filename"] == "user-document.pdf"
        assert response_body["content_type"] == "application/pdf"
        assert response_body["size"] == 48  # Length of binary content
        assert response_body["processable"] is True  # PDF is processable
        assert response_body["has_metadata"] is True
        assert response_body["ready_for_storage"] is True
