"""Tests for OpenAPI response fields enhancement (Issue #4870)"""

from typing import Optional

import pytest
from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.router import Router


def test_openapi_response_with_headers():
    """Test that response headers are properly included in OpenAPI schema"""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get(
        "/",
        responses={
            200: {
                "description": "Successful Response",
                "headers": {
                    "X-Rate-Limit": {
                        "description": "Rate limit header",
                        "schema": {"type": "integer"},
                    },
                    "X-Custom-Header": {
                        "description": "Custom header",
                        "schema": {"type": "string"},
                        "examples": {"example1": "value1"},
                    },
                },
            }
        },
    )
    def handler():
        return {"message": "hello"}

    schema = app.get_openapi_schema()
    response_dict = schema.paths["/"].get.responses[200]
    
    # Verify headers are present
    assert "headers" in response_dict
    headers = response_dict["headers"]
    
    # Check X-Rate-Limit header
    assert "X-Rate-Limit" in headers
    assert headers["X-Rate-Limit"]["description"] == "Rate limit header"
    assert headers["X-Rate-Limit"]["schema"]["type"] == "integer"
    
    # Check X-Custom-Header with examples
    assert "X-Custom-Header" in headers
    assert headers["X-Custom-Header"]["description"] == "Custom header"
    assert headers["X-Custom-Header"]["schema"]["type"] == "string"
    assert headers["X-Custom-Header"]["examples"]["example1"] == "value1"


def test_openapi_response_with_links():
    """Test that response links are properly included in OpenAPI schema"""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get(
        "/users/{user_id}",
        responses={
            200: {
                "description": "User details",
                "links": {
                    "GetUserOrders": {
                        "operationId": "getUserOrders",
                        "parameters": {"userId": "$response.body#/id"},
                        "description": "Get orders for this user",
                    }
                },
            }
        },
    )
    def get_user(user_id: str):
        return {"id": user_id, "name": "John Doe"}

    schema = app.get_openapi_schema()
    response = schema.paths["/users/{user_id}"].get.responses[200]
    
    # Verify links are present
    links = response.links
    
    assert "GetUserOrders" in links
    assert links["GetUserOrders"].operationId == "getUserOrders"
    assert links["GetUserOrders"].parameters["userId"] == "$response.body#/id"
    assert links["GetUserOrders"].description == "Get orders for this user"


def test_openapi_response_examples_preserved_with_model():
    """Test that examples are preserved when using model in response content"""
    app = APIGatewayRestResolver(enable_validation=True)

    class UserResponse(BaseModel):
        id: int
        name: str
        email: Optional[str] = None

    @app.get(
        "/",
        responses={
            200: {
                "description": "User response",
                "content": {
                    "application/json": {
                        "model": UserResponse,
                        "examples": {
                            "example1": {
                                "summary": "Example 1",
                                "value": {"id": 1, "name": "John", "email": "john@example.com"},
                            },
                            "example2": {
                                "summary": "Example 2",
                                "value": {"id": 2, "name": "Jane"},
                            },
                        },
                    }
                },
            }
        },
    )
    def handler() -> UserResponse:
        return UserResponse(id=1, name="Test")

    schema = app.get_openapi_schema()
    content = schema.paths["/"].get.responses[200].content["application/json"]
    
    # Verify model schema is present
    assert content.schema_.ref == "#/components/schemas/UserResponse"
    
    # Verify examples are preserved
    examples = content.examples
    
    assert "example1" in examples
    assert examples["example1"].summary == "Example 1"
    assert examples["example1"].value["id"] == 1
    assert examples["example1"].value["name"] == "John"
    
    assert "example2" in examples
    assert examples["example2"].summary == "Example 2"
    assert examples["example2"].value["id"] == 2


def test_openapi_response_encoding_preserved_with_model():
    """Test that encoding is preserved when using model in response content"""
    app = APIGatewayRestResolver(enable_validation=True)

    class FileUploadResponse(BaseModel):
        file_id: str
        filename: str
        content: bytes

    @app.post(
        "/upload",
        responses={
            200: {
                "description": "File upload response",
                "content": {
                    "multipart/form-data": {
                        "model": FileUploadResponse,
                        "encoding": {
                            "content": {
                                "contentType": "application/octet-stream",
                                "headers": {
                                    "X-Custom-Header": {
                                        "description": "Custom encoding header",
                                        "schema": {"type": "string"},
                                    }
                                },
                            }
                        },
                    }
                },
            }
        },
    )
    def upload_file() -> FileUploadResponse:
        return FileUploadResponse(file_id="123", filename="test.pdf", content=b"")

    schema = app.get_openapi_schema()
    content = schema.paths["/upload"].post.responses[200].content["multipart/form-data"]
    
    # Verify model schema is present
    assert content.schema_.ref == "#/components/schemas/FileUploadResponse"
    
    # Verify encoding is preserved
    encoding = content.encoding
    
    assert "content" in encoding
    assert encoding["content"].contentType == "application/octet-stream"
    assert encoding["content"].headers is not None
    assert "X-Custom-Header" in encoding["content"].headers


def test_openapi_response_all_fields_together():
    """Test response with headers, links, examples, and encoding all together"""
    app = APIGatewayRestResolver(enable_validation=True)

    class DataResponse(BaseModel):
        data: str
        timestamp: int

    @app.get(
        "/data",
        responses={
            200: {
                "description": "Data response with all fields",
                "headers": {
                    "X-Total-Count": {
                        "description": "Total count of items",
                        "schema": {"type": "integer"},
                    },
                    "X-Page": {
                        "description": "Current page",
                        "schema": {"type": "integer"},
                    },
                },
                "content": {
                    "application/json": {
                        "model": DataResponse,
                        "examples": {
                            "success": {
                                "summary": "Successful response",
                                "value": {"data": "test", "timestamp": 1234567890},
                            }
                        },
                        "encoding": {
                            "data": {
                                "contentType": "text/plain",
                            }
                        },
                    }
                },
                "links": {
                    "next": {
                        "operationId": "getNextPage",
                        "parameters": {"page": "$response.headers.X-Page + 1"},
                    }
                },
            }
        },
    )
    def get_data() -> DataResponse:
        return DataResponse(data="test", timestamp=1234567890)

    schema = app.get_openapi_schema()
    response = schema.paths["/data"].get.responses[200]
    
    # Check headers
    assert "X-Total-Count" in response.headers
    assert "X-Page" in response.headers
    
    # Check content with model, examples, and encoding
    content = response.content["application/json"]
    assert content.schema_.ref == "#/components/schemas/DataResponse"
    assert "success" in content.examples
    assert "data" in content.encoding
    
    # Check links
    assert "next" in response.links
    assert response.links["next"].operationId == "getNextPage"


def test_openapi_response_backward_compatibility():
    """Test that existing response definitions still work without new fields"""
    app = APIGatewayRestResolver(enable_validation=True)

    class SimpleResponse(BaseModel):
        message: str

    # Test 1: Simple response with just description
    @app.get("/simple", responses={200: {"description": "Simple response"}})
    def simple_handler():
        return {"message": "hello"}

    # Test 2: Response with model only
    @app.get(
        "/with-model",
        responses={
            200: {
                "description": "With model",
                "content": {"application/json": {"model": SimpleResponse}},
            }
        },
    )
    def model_handler() -> SimpleResponse:
        return SimpleResponse(message="test")

    # Test 3: Response with schema only
    @app.get(
        "/with-schema",
        responses={
            200: {
                "description": "With schema",
                "content": {
                    "application/json": {
                        "schema": {"type": "object", "properties": {"msg": {"type": "string"}}}
                    }
                },
            }
        },
    )
    def schema_handler():
        return {"msg": "test"}

    schema = app.get_openapi_schema()
    
    # Verify all endpoints work
    assert "/simple" in schema.paths
    assert "/with-model" in schema.paths
    assert "/with-schema" in schema.paths
    
    # Check simple response
    simple_response = schema.paths["/simple"].get.responses[200]
    assert simple_response.description == "Simple response"
    
    # Check model response
    model_response = schema.paths["/with-model"].get.responses[200]
    assert model_response.content["application/json"].schema_.ref == "#/components/schemas/SimpleResponse"
    
    # Check schema response
    schema_response = schema.paths["/with-schema"].get.responses[200]
    assert schema_response.content["application/json"].schema_.type == "object"


def test_openapi_response_empty_optional_fields():
    """Test that empty optional fields are handled correctly"""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get(
        "/empty",
        responses={
            200: {
                "description": "Response with empty optional fields",
                "headers": {},  # Empty headers
                "links": {},  # Empty links
                "content": {
                    "application/json": {
                        "schema": {"type": "object"},
                        "examples": {},  # Empty examples
                        "encoding": {},  # Empty encoding
                    }
                },
            }
        },
    )
    def empty_handler():
        return {}

    schema = app.get_openapi_schema()
    response = schema.paths["/empty"].get.responses[200]
    
    # Empty dicts should still be present in the schema
    assert response.headers == {}
    assert response.links == {}
    
    content = response.content["application/json"]
    
    # Check if examples and encoding are empty or None (both are valid)
    assert content.examples == {} or content.examples is None
    assert content.encoding == {} or content.encoding is None


def test_openapi_response_multiple_content_types_with_fields():
    """Test response with multiple content types each having their own fields"""
    app = APIGatewayRestResolver(enable_validation=True)

    class JsonResponse(BaseModel):
        data: str

    @app.get(
        "/multi-content",
        responses={
            200: {
                "description": "Multiple content types",
                "content": {
                    "application/json": {
                        "model": JsonResponse,
                        "examples": {
                            "json_example": {"value": {"data": "json_data"}},
                        },
                    },
                    "application/xml": {
                        "schema": {"type": "string"},
                        "examples": {
                            "xml_example": {"value": "<data>xml_data</data>"},
                        },
                    },
                    "text/plain": {
                        "schema": {"type": "string"},
                        "examples": {
                            "text_example": {"value": "plain text data"},
                        },
                    },
                },
            }
        },
    )
    def multi_content_handler():
        return {"data": "test"}

    schema = app.get_openapi_schema()
    response = schema.paths["/multi-content"].get.responses[200]
    
    # Check JSON content
    json_content = response.content["application/json"]
    assert json_content.schema_.ref == "#/components/schemas/JsonResponse"
    assert "json_example" in json_content.examples
    
    # Check XML content
    xml_content = response.content["application/xml"]
    assert xml_content.schema_.type == "string"
    assert "xml_example" in xml_content.examples
    
    # Check plain text content
    text_content = response.content["text/plain"]
    assert text_content.schema_.type == "string"
    assert "text_example" in text_content.examples


def test_openapi_response_with_router():
    """Test that new response fields work with Router"""
    app = APIGatewayRestResolver(enable_validation=True)
    router = Router()

    class RouterResponse(BaseModel):
        result: str

    @router.get(
        "/router-test",
        responses={
            200: {
                "description": "Router response",
                "headers": {
                    "X-Router-Header": {
                        "description": "Header from router",
                        "schema": {"type": "string"},
                    }
                },
                "content": {
                    "application/json": {
                        "model": RouterResponse,
                        "examples": {
                            "router_example": {"value": {"result": "from_router"}},
                        },
                    }
                },
            }
        },
    )
    def router_handler() -> RouterResponse:
        return RouterResponse(result="test")

    app.include_router(router)
    schema = app.get_openapi_schema()
    
    response = schema.paths["/router-test"].get.responses[200]
    
    # Verify headers
    assert "X-Router-Header" in response.headers
    
    # Verify content with model and examples
    content = response.content["application/json"]
    assert content.schema_.ref == "#/components/schemas/RouterResponse"
    assert "router_example" in content.examples