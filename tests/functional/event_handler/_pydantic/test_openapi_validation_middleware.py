import base64
import datetime
import json
import warnings
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePath
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import pytest
from pydantic import (
    AfterValidator,
    Base64UrlStr,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    StringConstraints,
    alias_generators,
)
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    LambdaFunctionUrlResolver,
    Response,
    VPCLatticeResolver,
    VPCLatticeV2Resolver,
)
from aws_lambda_powertools.event_handler.openapi.exceptions import ResponseValidationError
from aws_lambda_powertools.event_handler.openapi.params import Body, Form, Header, Path, Query
from tests.functional.utils import load_event


def test_validate_scalars(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int):
        print(user_id)

    # sending a number
    gw_event["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(gw_event, {})
    assert result["statusCode"] == 200

    # sending a string
    gw_event["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer", "int_parsing"])


def test_validate_pydantic_query_params(gw_event):
    """Test that Pydantic models in Query parameters are validated correctly"""

    app = APIGatewayRestResolver(enable_validation=True)
    del gw_event["multiValueQueryStringParameters"]

    class QueryParams(BaseModel):
        limit: int = Field(default=10, ge=1, le=100, description="Number of items")
        search: Optional[str] = Field(default=None, description="Search term")

    @app.get("/search")
    def search_handler(params: Annotated[QueryParams, Query()]):
        return {
            "limit": params.limit,
            "search": params.search,
        }

    # Test valid request
    gw_event["path"] = "/search"
    gw_event["queryStringParameters"] = {"limit": "25", "search": "python"}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["limit"] == 25
    assert body["search"] == "python"

    # Test with default values
    gw_event["queryStringParameters"] = {}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["limit"] == 10  # Default value
    assert body["search"] is None  # Default value

    # Test validation error (limit too high)
    gw_event["queryStringParameters"] = {"limit": "150"}

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    assert any("limit" in str(error) for error in body["detail"])


def test_validate_multi_value_query_params(gw_event):
    """Test that multi-value query parameters are validated correctly"""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/users")
    def users_handler(ids: Annotated[List[int], Query()]):
        return {"ids": ids}

    # Test valid request
    gw_event["path"] = "/users"
    gw_event["multiValueQueryStringParameters"] = {"ids": ["1", "2", "3"]}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["ids"] == [1, 2, 3]

    # Test with invalid value
    gw_event["multiValueQueryStringParameters"] = {"ids": ["1", "abc", "3"]}

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    assert any("ids" in str(error) for error in body["detail"])


def test_validate_pydantic_multi_value_query_params(gw_event):
    """Test that Pydantic models in Multi-Value Query parameters are validated correctly"""
    app = APIGatewayRestResolver(enable_validation=True)

    class QueryParams(BaseModel):
        ids: List[int] = Field(..., description="List of user IDs")

    @app.get("/users")
    def users_handler(params: Annotated[QueryParams, Query()]):
        return {"ids": params.ids}

    # Test valid request
    gw_event["path"] = "/users"
    gw_event["multiValueQueryStringParameters"] = {"ids": ["1", "2", "3"]}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["ids"] == [1, 2, 3]

    # Test with invalid value
    gw_event["multiValueQueryStringParameters"] = {"ids": ["1", "abc", "3"]}

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    assert any("ids" in str(error) for error in body["detail"])


def test_validate_pydantic_query_params_detailed_errors(gw_event):
    """Test that Pydantic validation errors include detailed field-level information"""
    app = APIGatewayRestResolver(enable_validation=True)

    del gw_event["multiValueHeaders"]
    del gw_event["multiValueQueryStringParameters"]

    class QueryParams(BaseModel):
        full_name: str = Field(..., min_length=5, description="Full name with minimum 5 characters")
        age: int = Field(..., ge=18, le=100, description="Age between 18 and 100")

    @app.get("/query-model")
    def query_model(params: Annotated[QueryParams, Query()]):
        return {"full_name": params.full_name, "age": params.age}

    # Test validation error with detailed field information
    gw_event["path"] = "/query-model"
    gw_event["queryStringParameters"] = {"full_name": "Jo", "age": "15"}  # Both invalid

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body

    # Check that we get detailed field-level errors
    errors = body["detail"]

    # Should have errors for both fields
    full_name_error = next((e for e in errors if "full_name" in e["loc"]), None)
    age_error = next((e for e in errors if "age" in e["loc"]), None)

    assert full_name_error is not None, "Should have error for full_name field"
    assert age_error is not None, "Should have error for age field"

    # Check error details for full_name
    assert full_name_error["loc"] == ["query", "params", "full_name"]
    assert full_name_error["type"] == "string_too_short"

    # Check error details for age
    assert age_error["loc"] == ["query", "params", "age"]
    assert age_error["type"] == "greater_than_equal"


def test_validate_pydantic_header_params(gw_event):
    """Test that Pydantic models in Header parameters are validated correctly"""
    app = APIGatewayRestResolver(enable_validation=True)

    del gw_event["multiValueHeaders"]

    class HeaderParams(BaseModel):
        authorization: str = Field(description="Authorization token")
        user_agent: str = Field(default="PowerTools/1.0", description="User agent")

    @app.get("/protected")
    def protected_handler(my_headers: Annotated[HeaderParams, Header()]):
        return {
            "authorization": my_headers.authorization,
            "user_agent": my_headers.user_agent,
        }

    # Test valid request
    gw_event["path"] = "/protected"
    gw_event["headers"] = {"authorization": "Bearer token123", "user-agent": "TestClient/1.0"}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["authorization"] == "Bearer token123"
    assert body["user_agent"] == "TestClient/1.0"

    # Test with default value
    gw_event["headers"] = {"authorization": "Bearer token123"}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["authorization"] == "Bearer token123"
    assert body["user_agent"] == "PowerTools/1.0"  # Default value

    # Test missing required header
    gw_event["headers"] = {}

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    assert any("my-headers" in str(error) for error in body["detail"])


def test_validate_multi_value_header_params(gw_event):
    """Test that multi-value headers are validated correctly without Pydantic"""
    app = APIGatewayRestResolver(enable_validation=True)

    del gw_event["multiValueHeaders"]

    @app.get("/multi-value-headers")
    def multi_value_handler(my_headers: Annotated[List[str], Header()]):
        return {"items": my_headers}

    # Test valid request
    gw_event["path"] = "/multi-value-headers"
    gw_event["multiValueHeaders"] = {"my-headers": ["item1", "item2"]}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["items"] == ["item1", "item2"]

    # Test invalid request
    gw_event["multiValueHeaders"] = {"items": "invalid"}

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    assert any("my-headers" in str(error) for error in body["detail"])


def test_validate_pydantic_multi_value_header_params(gw_event):
    """Test that multi-value headers are validated correctly"""
    app = APIGatewayRestResolver(enable_validation=True)

    del gw_event["multiValueHeaders"]

    class MultiValueHeaderParams(BaseModel):
        list_items: List[str] = Field(description="List of items")

    @app.get("/multi-value-headers")
    def multi_value_handler(my_headers: Annotated[MultiValueHeaderParams, Header()]):
        return {"items": my_headers.list_items}

    # Test valid request
    gw_event["path"] = "/multi-value-headers"
    gw_event["multiValueHeaders"] = {"list-items": ["item1", "item2"]}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["items"] == ["item1", "item2"]

    # Test invalid request
    gw_event["multiValueHeaders"] = {"items": "invalid"}

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    assert any("my-headers" in str(error) for error in body["detail"])


def test_validate_pydantic_header_snake_case_to_kebab_case_schema(gw_event):
    """Test that snake_case header fields are converted to kebab-case in OpenAPI schema and validation"""
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger()

    class HeaderParams(BaseModel):
        correlation_id: str = Field(description="Correlation ID header")
        user_agent: str = Field(default="PowerTools/1.0", description="User agent header")
        accept: str = Field(default="application/json")  # omit description to test optional description

    @app.get("/kebab-headers")
    def kebab_handler(my_headers: Annotated[HeaderParams, Header()]):
        return {
            "correlation_id": my_headers.correlation_id,
            "user_agent": my_headers.user_agent,
        }

    # Test that OpenAPI schema uses kebab-case for headers
    openapi_schema = app.get_openapi_schema()
    operation = openapi_schema.paths["/kebab-headers"].get
    parameters = operation.parameters

    # Find the correlation_id parameter
    correlation_param = next((p for p in parameters if p.name == "correlation-id"), None)
    assert correlation_param is not None, "Should have correlation-id parameter in kebab-case"

    # Find the user_agent parameter
    user_agent_param = next((p for p in parameters if p.name == "user-agent"), None)
    assert user_agent_param is not None, "Should have user-agent parameter in kebab-case"

    # Test validation with kebab-case headers
    gw_event["path"] = "/kebab-headers"
    gw_event["multiValueHeaders"] = {"correlation-id": "test-123", "user-agent": "TestClient/1.0"}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["correlation_id"] == "test-123"
    assert body["user_agent"] == "TestClient/1.0"


def test_validate_pydantic_mixed_params(gw_event):
    """Test that mixed Pydantic models (Query + Header) are validated correctly"""
    app = APIGatewayRestResolver(enable_validation=True)

    del gw_event["multiValueHeaders"]
    del gw_event["multiValueQueryStringParameters"]

    class QueryParams(BaseModel):
        q: str = Field(description="Search query")
        limit: int = Field(default=10, description="Number of results")

    class HeaderParams(BaseModel):
        authorization: str = Field(description="Bearer token")

    @app.get("/mixed")
    def mixed_handler(query: Annotated[QueryParams, Query()], headers: Annotated[HeaderParams, Header()]):
        return {
            "query": {"q": query.q, "limit": query.limit},
            "headers": {"authorization": headers.authorization},
        }

    # Test valid request
    gw_event["path"] = "/mixed"
    gw_event["queryStringParameters"] = {"q": "python", "limit": "25"}
    gw_event["headers"] = {"authorization": "Bearer token123"}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["query"]["q"] == "python"
    assert body["query"]["limit"] == 25
    assert body["headers"]["authorization"] == "Bearer token123"

    # Test missing required query parameter
    gw_event["queryStringParameters"] = {"limit": "25"}  # Missing 'q'

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    assert any("q" in str(error) for error in body["detail"])

    # Test missing required header
    gw_event["queryStringParameters"] = {"q": "python"}
    gw_event["headers"] = {}  # Missing 'authorization'

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    assert any("headers" in str(error) for error in body["detail"])


def test_validate_pydantic_with_alias(gw_event):
    """Test that Pydantic models with field aliases work correctly"""
    app = APIGatewayRestResolver(enable_validation=True)

    del gw_event["multiValueHeaders"]
    del gw_event["multiValueQueryStringParameters"]

    class HeaderParams(BaseModel):
        accept_language: str = Field(alias="accept-language", description="Language preference")

    @app.get("/alias")
    def alias_handler(headers: Annotated[HeaderParams, Header()]):
        return {"accept_language": headers.accept_language}

    # Test with alias in request
    gw_event["path"] = "/alias"
    gw_event["headers"] = {"accept-language": "en-US"}

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["accept_language"] == "en-US"

    # Test missing aliased field
    gw_event["headers"] = {}

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    assert any("headers" in str(error) for error in body["detail"])


def test_validate_scalars_with_default(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int = 123):
        print(user_id)

    # sending a number
    gw_event["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(gw_event, {})
    assert result["statusCode"] == 200

    # sending a string
    gw_event["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer", "int_parsing"])


def test_validate_scalars_with_default_and_optional(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int = 123, include_extra: bool = False):
        print(user_id)

    # sending a number
    gw_event["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(gw_event, {})
    assert result["statusCode"] == 200

    # sending a string
    gw_event["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer", "int_parsing"])


def test_validate_return_type(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a return type
    @app.get("/")
    def handler() -> int:
        return 123

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be 123
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert result["body"] == "123"


def test_validate_return_list(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a return type
    @app.get("/")
    def handler() -> List[int]:
        return [123, 234]

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be [123, 234]
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == [123, 234]


def test_validate_return_tuple(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    sample_tuple = (1, 2, 3)

    # WHEN a handler is defined with a return type as Tuple
    @app.get("/")
    def handler() -> Tuple:
        return sample_tuple

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a tuple
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == [1, 2, 3]


def test_validate_return_purepath(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    sample_path = PurePath(__file__)

    # WHEN a handler is defined with a return type as string
    # WHEN return value is a PurePath
    @app.get("/")
    def handler() -> str:
        return sample_path.as_posix()

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a string
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert result["body"] == sample_path.as_posix()


def test_validate_return_enum(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(Enum):
        name = "powertools"

    # WHEN a handler is defined with a return type as Enum
    @app.get("/")
    def handler() -> Model:
        return Model.name.value

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a string
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert result["body"] == "powertools"


def test_validate_return_dataclass(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    @dataclass
    class Model:
        name: str
        age: int

    # WHEN a handler is defined with a return type as dataclass
    @app.get("/")
    def handler() -> Model:
        return Model(name="John", age=30)

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_return_model(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a return type as Pydantic model
    @app.get("/")
    def handler() -> Model:
        return Model(name="John", age=30)

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_invalid_return_model(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a return type as Pydantic model
    @app.get("/")
    def handler() -> Model:
        return {"name": "John"}  # type: ignore

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 422
    # THEN the body must be a dict
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


def test_validate_body_param(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Model:
        return user

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_body_param_with_stripped_headers(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    # WHEN headers has spaces
    @app.post("/")
    def handler(user: Model) -> Model:
        return user

    gw_event["httpMethod"] = "POST"
    gw_event["headers"] = {"Content-type": " application/json "}
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_unsupported_content_type_headers(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    # WHEN headers has unsupported content-type
    @app.post("/")
    def handler(user: Model) -> Model:
        return user

    gw_event["httpMethod"] = "POST"
    gw_event["headers"] = {"Content-type": "text/fake-content-type"}
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should return 415 (Unsupported Media Type)
    # THEN the body must have the "unsupported_content_type" error message
    result = app(gw_event, {})
    assert result["statusCode"] == 415
    assert "unsupported_content_type" in result["body"]


def test_validate_body_param_with_invalid_date(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Model:
        return user

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = "{"  # invalid JSON

    # THEN the handler should be invoked and return 422
    # THEN the body must have the "json_invalid" error message
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert "json_invalid" in result["body"]


def test_validate_embed_body_param(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Annotated[Model, Body(embed=True)]) -> Model:
        return user

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 422
    # THEN the body must be a dict
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]

    # THEN the handler should be invoked and return 200
    # THEN the body must be a dict
    gw_event["body"] = json.dumps({"user": {"name": "John", "age": 30}})
    result = app(gw_event, {})
    assert result["statusCode"] == 200


def test_validate_body_param_with_missing_body(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with multiple body parameters
    @app.post("/")
    def handler(name: str, age: int):
        return {"name": name, "age": age}

    # WHEN the event has no body
    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = None  # simulate event without body
    gw_event["headers"]["content-type"] = "application/json"

    result = app(gw_event, {})

    # THEN the handler should be invoked and return 422
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


def test_validate_body_param_with_empty_body(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with multiple body parameters
    @app.post("/")
    def handler(name: str, age: int):
        return {"name": name, "age": age}

    # WHEN the event has no body
    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = "[]"  # JSON array -> received_body is a list (no .get)
    gw_event["headers"]["content-type"] = "application/json"

    result = app(gw_event, {})

    # THEN the handler should be invoked and return 422
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


def test_validate_embed_body_param_with_missing_body(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Annotated[Model, Body(embed=True)]) -> Model:
        return user

    # WHEN the event has no body
    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = None  # simulate event without body
    gw_event["headers"]["content-type"] = "application/json"

    result = app(gw_event, {})

    # THEN the handler should be invoked and return 422
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


def test_validate_embed_body_param_with_empty_body(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Annotated[Model, Body(embed=True)]) -> Model:
        return user

    # WHEN the event has no body
    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = "[]"  # JSON array -> received_body is a list (no .get)
    gw_event["headers"]["content-type"] = "application/json"

    result = app(gw_event, {})

    # THEN the handler should be invoked and return 422
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


def test_validate_response_return(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Response[Model]:
        return Response(body=user, status_code=200, content_type="application/json")

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a dict
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_response_invalid_return(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Response[Model]:
        return Response(body=user, status_code=200)

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({})

    # THEN the handler should be invoked and return 422
    # THEN the body should have the word missing
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


########### TEST WITH QUERY PARAMS
@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_without_query_params", 200, None),
    ],
)
def test_validation_query_string_with_api_rest_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event,
):
    # GIVEN a APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    gw_event["httpMethod"] = "GET"
    gw_event["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(parameter1: Annotated[List[str], Query()], parameter2: str):
            print(parameter2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(parameter1: Annotated[List[int], Query()], parameter2: str):
            print(parameter2)

    # Define handler3 without params
    if handler_func == "handler3_without_query_params":
        gw_event["queryStringParameters"] = None
        gw_event["multiValueQueryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_without_query_params", 200, None),
    ],
)
def test_validation_query_string_with_api_http_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_http,
):
    # GIVEN a APIGatewayHttpResolver with validation enabled
    app = APIGatewayHttpResolver(enable_validation=True)

    gw_event_http["rawPath"] = "/users"
    gw_event_http["requestContext"]["http"]["method"] = "GET"
    gw_event_http["requestContext"]["http"]["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(parameter1: Annotated[List[str], Query()], parameter2: str):
            print(parameter2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(parameter1: Annotated[List[int], Query()], parameter2: str):
            print(parameter2)

    # Define handler3 without params
    if handler_func == "handler3_without_query_params":
        gw_event_http["queryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_http, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_without_query_params", 200, None),
    ],
)
def test_validation_query_string_with_alb_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_alb,
):
    # GIVEN a ALBResolver with validation enabled
    app = ALBResolver(enable_validation=True)

    gw_event_alb["path"] = "/users"

    # WHEN a handler is defined with various parameters and routes
    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(parameter1: Annotated[List[str], Query()], parameter2: str):
            print(parameter2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(parameter1: Annotated[List[int], Query()], parameter2: str):
            print(parameter2)

    # Define handler3 without params
    if handler_func == "handler3_without_query_params":
        gw_event_alb["multiValueQueryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_alb, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


def test_validation_query_string_with_encoded_datetime_alb_resolver():
    # GIVEN a ALBResolver with validation enabled,
    # and an event with a url-encoded datetime
    # as a query string parameter
    app = ALBResolver(enable_validation=True, decode_query_parameters=True)
    raw_event = load_event("albEvent.json")
    raw_event["path"] = "/users"
    raw_event["queryStringParameters"] = {"query_dt": "2025-12-20T16%3A56%3A02.032000"}

    # WHEN a handler is defined with various parameters and routes
    @app.get("/users")
    def handler(query_dt: datetime.datetime):
        return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(raw_event, {})
    assert result["statusCode"] == 200


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_without_query_params", 200, None),
    ],
)
def test_validation_query_string_with_lambda_url_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_lambda_url,
):
    # GIVEN a LambdaFunctionUrlResolver with validation enabled
    app = LambdaFunctionUrlResolver(enable_validation=True)

    gw_event_lambda_url["rawPath"] = "/users"
    gw_event_lambda_url["requestContext"]["http"]["method"] = "GET"
    gw_event_lambda_url["requestContext"]["http"]["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(parameter1: Annotated[List[str], Query()], parameter2: str):
            print(parameter2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(parameter1: Annotated[List[int], Query()], parameter2: str):
            print(parameter2)

    # Define handler3 without params
    if handler_func == "handler3_without_query_params":
        gw_event_lambda_url["queryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_lambda_url, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_without_query_params", 200, None),
    ],
)
def test_validation_query_string_with_vpc_lattice_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_vpc_lattice,
):
    # GIVEN a VPCLatticeV2Resolver with validation enabled
    app = VPCLatticeV2Resolver(enable_validation=True)

    gw_event_vpc_lattice["path"] = "/users"

    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(parameter1: Annotated[List[str], Query()], parameter2: str):
            print(parameter2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(parameter1: Annotated[List[int], Query()], parameter2: str):
            print(parameter2)

    # Define handler3 without params
    if handler_func == "handler3_without_query_params":
        gw_event_vpc_lattice["queryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_vpc_lattice, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


########### TEST WITH HEADER PARAMS
@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_api_rest_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event,
):
    # GIVEN a APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    gw_event["httpMethod"] = "GET"
    gw_event["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(alias="Header2")],
            header1: Annotated[str, Header(alias="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        gw_event["headers"] = None
        gw_event["multiValueHeaders"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_http_rest_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_http,
):
    # GIVEN a APIGatewayHttpResolver with validation enabled
    app = APIGatewayHttpResolver(enable_validation=True)

    gw_event_http["rawPath"] = "/users"
    gw_event_http["requestContext"]["http"]["method"] = "GET"
    gw_event_http["requestContext"]["http"]["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(alias="Header2")],
            header1: Annotated[str, Header(alias="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        gw_event_http["headers"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_http, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_alb_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_alb,
):
    # GIVEN a ALBResolver with validation enabled
    app = ALBResolver(enable_validation=True)

    gw_event_alb["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(alias="Header2")],
            header1: Annotated[str, Header(alias="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        gw_event_alb["multiValueHeaders"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_alb, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_lambda_url_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_lambda_url,
):
    # GIVEN a LambdaFunctionUrlResolver with validation enabled
    app = LambdaFunctionUrlResolver(enable_validation=True)

    gw_event_lambda_url["rawPath"] = "/users"
    gw_event_lambda_url["requestContext"]["http"]["method"] = "GET"
    gw_event_lambda_url["requestContext"]["http"]["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(alias="Header2")],
            header1: Annotated[str, Header(alias="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        gw_event_lambda_url["headers"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_lambda_url, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_vpc_lattice_v1_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_vpc_lattice_v1,
):
    # GIVEN a VPCLatticeResolver with validation enabled
    app = VPCLatticeResolver(enable_validation=True)

    gw_event_vpc_lattice_v1["raw_path"] = "/users"
    gw_event_vpc_lattice_v1["method"] = "GET"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(alias="Header2")],
            header1: Annotated[str, Header(alias="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        gw_event_vpc_lattice_v1["headers"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_vpc_lattice_v1, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_vpc_lattice_v2_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_vpc_lattice,
):
    # GIVEN a VPCLatticeV2Resolver with validation enabled
    app = VPCLatticeV2Resolver(enable_validation=True)

    gw_event_vpc_lattice["path"] = "/users"
    gw_event_vpc_lattice["method"] = "GET"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(alias="Header2")],
            header1: Annotated[str, Header(alias="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        gw_event_vpc_lattice["headers"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_vpc_lattice, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


def test_validate_with_minimal_event():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int = 123):
        print(user_id)

    minimal_event = {
        "path": "/users/123",
        "httpMethod": "GET",
        "requestContext": {"requestId": "227b78aa-779d-47d4-a48e-ce62120393b8"},  # correlation ID
    }

    # THEN the handler should be invoked and return 200
    result = app(minimal_event, {})
    assert result["statusCode"] == 200


def test_validate_list_response(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    response_before_validation = [
        {
            "name": "Joe",
            "age": 20,
        },
        {
            "name": "Jane",
            "age": 20,
        },
    ]

    @app.get("/list_response_with_same_element_types")
    def handler_different_list() -> List[Model]:
        return response_before_validation

    # WHEN returning list with the same element type as the non-Optional return type
    gw_event["path"] = "/list_response_with_same_element_types"
    result = app(gw_event, {})
    body = json.loads(result["body"])

    # THEN it should return a validation error
    assert result["statusCode"] == 200
    assert body == response_before_validation


def test_validation_error_none_returned_non_optional_type(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    @app.get("/none_not_allowed")
    def handler_none_not_allowed() -> Model:
        return None  # type: ignore

    # WHEN returning None for a non-Optional type
    gw_event["path"] = "/none_not_allowed"
    result = app(gw_event, {})

    # THEN it should return a validation error
    assert result["statusCode"] == 422
    body = json.loads(result["body"])
    assert body["detail"][0]["type"] == "model_attributes_type"
    assert body["detail"][0]["loc"] == ["response"]


def test_validation_error_different_list_returned_non_optional_type(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    different_list_response = ["a", "b", "c"]

    @app.get("/list_response_with_different_element_types")
    def handler_different_list() -> List[Model]:
        return different_list_response

    # WHEN returning list with the different element type as the non-Optional return type
    gw_event["path"] = "/list_response_with_different_element_types"
    result = app(gw_event, {})

    # THEN it should return a validation error
    assert result["statusCode"] == 422
    body = json.loads(result["body"])
    assert len(body["detail"]) == len(different_list_response)
    assert body["detail"][0]["type"] == "model_attributes_type"
    assert body["detail"][0]["loc"] == ["response", 0]


def test_validation_error_incomplete_model_returned_non_optional_type(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    @app.get("/incomplete_model_not_allowed")
    def handler_incomplete_model_not_allowed() -> Model:
        return {"age": 18}  # type: ignore

    # WHEN returning incomplete model for a non-Optional type
    gw_event["path"] = "/incomplete_model_not_allowed"
    result = app(gw_event, {})

    # THEN it should return a validation error
    assert result["statusCode"] == 422
    body = json.loads(result["body"])
    assert "missing" in body["detail"][0]["type"]
    assert "name" in body["detail"][0]["loc"]


def test_none_returned_for_optional_type(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    @app.get("/none_allowed")
    def handler_none_allowed() -> Optional[Model]:
        return None

    # WHEN returning None for an Optional type
    gw_event["path"] = "/none_allowed"
    result = app(gw_event, {})

    # THEN it should succeed
    assert result["statusCode"] == 200
    assert result["body"] == "null"


@pytest.mark.parametrize(
    "path, body",
    [
        ("/empty_dict", {}),
        ("/empty_list", []),
        ("/none", "null"),
        ("/empty_string", ""),
    ],
    ids=["empty_dict", "empty_list", "none", "empty_string"],
)
def test_none_returned_for_falsy_return(gw_event, path, body):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    @app.get(path)
    def handler_none_allowed() -> Model:
        return body

    # WHEN returning None for an Optional type
    gw_event["path"] = path
    result = app(gw_event, {})

    # THEN it should succeed
    assert result["statusCode"] == 422


def test_custom_response_validation_error_http_code_valid_response(gw_event):
    # GIVEN an APIGatewayRestResolver with custom response validation enabled
    app = APIGatewayRestResolver(enable_validation=True, response_validation_error_http_code=422)

    class Model(BaseModel):
        name: str
        age: int

    @app.get("/valid_response")
    def handler_valid_response() -> Model:
        return {
            "name": "Joe",
            "age": 18,
        }  # type: ignore

    # WHEN returning the expected type
    gw_event["path"] = "/valid_response"
    result = app(gw_event, {})

    # THEN it should return a 200 OK
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body == {"name": "Joe", "age": 18}


@pytest.mark.parametrize(
    "http_code",
    (422, 500, 510),
)
def test_custom_response_validation_error_http_code_invalid_response_none(
    http_code,
    gw_event,
):
    # GIVEN an APIGatewayRestResolver with custom response validation enabled
    app = APIGatewayRestResolver(enable_validation=True, response_validation_error_http_code=http_code)

    class Model(BaseModel):
        name: str
        age: int

    @app.get("/none_not_allowed")
    def handler_none_not_allowed() -> Model:
        return None  # type: ignore

    # WHEN returning None for a non-Optional type
    gw_event["path"] = "/none_not_allowed"
    result = app(gw_event, {})

    # THEN it should return a validation error with the custom status code provided
    assert result["statusCode"] == http_code
    body = json.loads(result["body"])
    assert body["detail"][0]["type"] == "model_attributes_type"
    assert body["detail"][0]["loc"] == ["response"]


@pytest.mark.parametrize(
    "http_code",
    (422, 500, 510),
)
def test_custom_response_validation_error_http_code_invalid_response_incomplete_model(
    http_code,
    gw_event,
):
    # GIVEN an APIGatewayRestResolver with custom response validation enabled
    app = APIGatewayRestResolver(enable_validation=True, response_validation_error_http_code=http_code)

    class Model(BaseModel):
        name: str
        age: int

    @app.get("/incomplete_model_not_allowed")
    def handler_incomplete_model_not_allowed() -> Model:
        return {"age": 18}  # type: ignore

    # WHEN returning incomplete model for a non-Optional type
    gw_event["path"] = "/incomplete_model_not_allowed"
    result = app(gw_event, {})

    # THEN it should return a validation error with the custom status code provided
    assert result["statusCode"] == http_code
    body = json.loads(result["body"])
    assert body["detail"][0]["type"] == "missing"
    assert body["detail"][0]["loc"] == ["response", "name"]


@pytest.mark.parametrize(
    "http_code",
    (422, 500, 510),
)
def test_custom_response_validation_error_sanitized_response(
    http_code,
    gw_event,
):
    # GIVEN an APIGatewayRestResolver with custom response validation enabled
    # with a sanitized response validation error response
    app = APIGatewayRestResolver(enable_validation=True, response_validation_error_http_code=http_code)

    class Model(BaseModel):
        name: str
        age: int

    @app.get("/incomplete_model_not_allowed")
    def handler_incomplete_model_not_allowed() -> Model:
        return {"age": 18}  # type: ignore

    @app.exception_handler(ResponseValidationError)
    def handle_response_validation_error(ex: ResponseValidationError):
        return Response(
            status_code=500,
            body="Unexpected response.",
        )

    # WHEN returning incomplete model for a non-Optional type
    gw_event["path"] = "/incomplete_model_not_allowed"
    result = app(gw_event, {})

    # THEN it should return the sanitized response
    assert result["statusCode"] == 500
    assert result["body"] == "Unexpected response."


def test_custom_response_validation_error_no_validation():
    # GIVEN an APIGatewayRestResolver with validation not enabled
    # setting a custom http status code for response validation must raise a ValueError
    with pytest.raises(ValueError) as exception_info:
        APIGatewayRestResolver(response_validation_error_http_code=500)

    assert (
        str(exception_info.value)
        == "'response_validation_error_http_code' cannot be set when enable_validation is False."
    )


@pytest.mark.parametrize("response_validation_error_http_code", [(20), ("hi"), (1.21)])
def test_custom_response_validation_error_bad_http_code(response_validation_error_http_code):
    # GIVEN an APIGatewayRestResolver with validation enabled
    # setting custom status code for response validation that is not a valid HTTP code must raise a ValueError
    with pytest.raises(ValueError) as exception_info:
        APIGatewayRestResolver(
            enable_validation=True,
            response_validation_error_http_code=response_validation_error_http_code,
        )

    assert (
        str(exception_info.value)
        == f"'{response_validation_error_http_code}' must be an integer representing an HTTP status code."
    )


def test_custom_route_response_validation_error_custom_route_and_app_with_default_validation(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    @app.get("/incomplete_model_not_allowed")
    def handler_incomplete_model_not_allowed() -> Model:
        return {"age": 18}  # type: ignore

    # HAVING route with custom response validation error
    @app.get(
        "/custom_incomplete_model_not_allowed",
        custom_response_validation_http_code=500,
    )
    def handler_custom_route_response_validation_error() -> Model:
        return {"age": 18}  # type: ignore

    # WHEN returning incomplete model for a non-Optional type
    gw_event["path"] = "/incomplete_model_not_allowed"
    result = app(gw_event, {})

    gw_event["path"] = "/custom_incomplete_model_not_allowed"
    custom_result = app(gw_event, {})

    # THEN it must return a validation error with the custom status code provided
    assert result["statusCode"] == 422
    assert custom_result["statusCode"] == 500
    assert json.loads(result["body"])["detail"] == json.loads(custom_result["body"])["detail"]


def test_custom_route_response_validation_error_sanitized_response(gw_event):
    # GIVEN an APIGatewayRestResolver with custom response validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    @app.get(
        "/custom_incomplete_model_not_allowed",
        custom_response_validation_http_code=422,
    )
    def handler_custom_route_response_validation_error() -> Model:
        return {"age": 18}  # type: ignore

    # HAVING a sanitized response validation error response
    @app.exception_handler(ResponseValidationError)
    def handle_response_validation_error(ex: ResponseValidationError):
        return Response(
            status_code=500,
            body="Unexpected response.",
        )

    # WHEN returning incomplete model for a non-Optional type
    gw_event["path"] = "/custom_incomplete_model_not_allowed"
    result = app(gw_event, {})

    # THEN it must return the sanitized response
    assert result["statusCode"] == 500
    assert result["body"] == "Unexpected response."


def test_custom_route_response_validation_error_with_app_custom_response_validation(gw_event):
    # GIVEN an APIGatewayRestResolver with validation and custom response validation enabled
    app = APIGatewayRestResolver(enable_validation=True, response_validation_error_http_code=500)

    class Model(BaseModel):
        name: str
        age: int

    # HAVING a route with custom response validation
    @app.get(
        "/custom_incomplete_model_not_allowed",
        custom_response_validation_http_code=422,
    )
    def handler_custom_route_response_validation_error() -> Model:
        return {"age": 18}  # type: ignore

    # WHEN returning incomplete model for a non-Optional type on route with custom response validation
    gw_event["path"] = "/custom_incomplete_model_not_allowed"
    result = app(gw_event, {})

    # THEN route's custom response validation must take precedence over the app's.
    assert result["statusCode"] == 422
    body = json.loads(result["body"])
    assert body["detail"][0]["type"] == "missing"
    assert body["detail"][0]["loc"] == ["response", "name"]


def test_custom_route_response_validation_error_no_app_validation():
    # GIVEN an APIGatewayRestResolver with validation not enabled
    with pytest.raises(ValueError) as exception_info:
        app = APIGatewayRestResolver()

        class Model(BaseModel):
            name: str
            age: int

        # HAVING a route with custom response validation http code
        @app.get(
            "/custom_incomplete_model_not_allowed",
            custom_response_validation_http_code=422,
        )
        def handler_custom_route_response_validation_error() -> Model:
            return {"age": 18}  # type: ignore

    # THEN it must raise ValueError describing the issue
    assert (
        str(exception_info.value)
        == "'custom_response_validation_http_code' cannot be set for route when enable_validation is False on resolver."
    )


@pytest.mark.parametrize("response_validation_error_http_code", [(20), ("hi"), (1.21), (True), (False)])
def test_custom_route_response_validation_error_bad_http_code(response_validation_error_http_code):
    # GIVEN an APIGatewayRestResolver with validation enabled
    with pytest.raises(ValueError) as exception_info:
        app = APIGatewayRestResolver(enable_validation=True)

        class Model(BaseModel):
            name: str
            age: int

        # HAVING a route with custom response validation which is not a valid HTTP code
        @app.get(
            "/custom_incomplete_model_not_allowed",
            custom_response_validation_http_code=response_validation_error_http_code,
        )
        def handler_custom_route_response_validation_error() -> Model:
            return {"age": 18}  # type: ignore

    # THEN it must raise ValueError describing the issue
    assert (
        str(exception_info.value)
        == f"'{response_validation_error_http_code}' must be an integer representing an HTTP status code or an enum of type HTTPStatus."  # noqa: E501
    )


def test_parse_form_data_url_encoded(gw_event):
    """Test _parse_form_data method with URL-encoded form data"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/form")
    def post_form(name: Annotated[str, Form()], tags: Annotated[List[str], Form()]):
        return {"name": name, "tags": tags}

    # WHEN sending a POST request with URL-encoded form data
    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/form"
    gw_event["headers"]["content-type"] = "application/x-www-form-urlencoded"
    gw_event["body"] = "name=test&tags=tag1&tags=tag2"

    result = app(gw_event, {})

    # THEN it should parse the form data correctly
    assert result["statusCode"] == 200
    assert result["body"] == '{"name":"test","tags":["tag1","tag2"]}'

    # WHEN sending a POST request with a single value for a list field
    gw_event["body"] = "name=test&tags=tag1"

    result = app(gw_event, {})

    # THEN it should parse the form data correctly
    assert result["statusCode"] == 200
    assert result["body"] == '{"name":"test","tags":["tag1"]}'


def test_parse_form_data_wrong_value(gw_event):
    """Test _parse_form_data method with URL-encoded form data"""

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/form")
    def post_form(name: Annotated[str, Form()], tags: Annotated[List[str], Form()]):
        return {"name": name, "tags": tags}

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/form"
    gw_event["headers"]["content-type"] = "application/x-www-form-urlencoded"
    gw_event["body"] = "123"

    result = app(gw_event, {})
    assert result["statusCode"] == 422


def test_parse_form_data_empty_body(gw_event):
    """Test _parse_form_data method with empty body"""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/form")
    def post_form(name: Annotated[str, Form()] = "default"):
        return {"name": name}

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/form"
    gw_event["headers"]["content-type"] = "application/x-www-form-urlencoded"
    gw_event["body"] = ""

    result = app(gw_event, {})
    assert result["statusCode"] == 200


def test_form_data_parsing_exception(gw_event):
    """Test _parse_form_data method exception handling"""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/form")
    def post_form(name: Annotated[str, Form()]):
        return {"name": name}

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/form"
    gw_event["headers"]["content-type"] = "application/x-www-form-urlencoded"
    # Set body to None to trigger exception handling
    gw_event["body"] = None

    result = app(gw_event, {})
    assert result["statusCode"] == 422
    # With None body, it becomes empty string and missing field validation triggers
    assert "missing" in result["body"]


def test_prepare_response_content_nested_structures():
    """Test _prepare_response_content method with nested data structures"""
    from dataclasses import dataclass

    app = APIGatewayRestResolver(enable_validation=True)

    @dataclass
    class TestDataclass:
        name: str
        value: int

    class TestModel(BaseModel):
        title: str
        count: int

    @app.get("/complex")
    def get_complex() -> dict:
        # Return complex nested structure to trigger _prepare_response_content paths
        return {
            "models": [TestModel(title="test1", count=1), TestModel(title="test2", count=2)],
            "dataclasses": [TestDataclass(name="dc1", value=10)],
            "nested_dicts": {"inner": {"key": "value"}},
            "mixed_list": [{"a": 1}, TestModel(title="mixed", count=3)],
        }

    event = {
        "httpMethod": "GET",
        "path": "/complex",
        "headers": {},
        "queryStringParameters": None,
        "body": None,
        "isBase64Encoded": False,
        "requestContext": {"requestId": "test"},
        "pathParameters": None,
    }

    result = app(event, {})
    assert result["statusCode"] == 200


def test_multipart_empty_parts(gw_event):
    """Test handling of multipart data with empty parts."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/test")
    def handler():
        return {"status": "ok"}

    content_type = "multipart/form-data; boundary=----boundary"

    # Test with completely empty multipart content
    empty_multipart = "------boundary--\r\n"
    gw_event["body"] = base64.b64encode(empty_multipart.encode()).decode()
    gw_event["headers"]["content-type"] = content_type
    gw_event["isBase64Encoded"] = True
    gw_event["path"] = "/test"
    gw_event["httpMethod"] = "POST"

    result = app(gw_event, {})
    assert result["statusCode"] == 200


def test_response_serialization_with_custom_serializer():
    """Test response serialization using custom serializer path."""
    app = APIGatewayRestResolver(enable_validation=True)

    class CustomModel(BaseModel):
        id: int
        name: str

        def dict(self, **kwargs):
            # Custom dict method that triggers alternative serialization path
            return {"custom": "value", "id": self.id, "name": self.name}

    @app.get("/test")
    def handler() -> CustomModel:
        return CustomModel(id=1, name="test")

    result = app({"httpMethod": "GET", "path": "/test"}, {})
    assert result["statusCode"] == 200


def test_middleware_early_return_without_validation_error(gw_event):
    """Test that middleware can return early response without triggering validation error (Issue #5228)"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)
    execution_log = []

    def auth_middleware(app, next_middleware):
        execution_log.append("auth_middleware")
        # Return 401 without calling next_middleware - should not trigger validation
        return Response(status_code=401, content_type="application/json", body="{}")

    def logging_middleware(app, next_middleware):
        execution_log.append("logging_middleware")  # Should not be called
        return next_middleware(app)

    app.use(middlewares=[auth_middleware, logging_middleware])

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    @app.get("/protected")
    def protected_route() -> UserModel:
        execution_log.append("route_handler")  # Should not be called
        return UserModel(name="John", age=30, email="john@example.com")

    # WHEN calling the protected route
    gw_event["path"] = "/protected"
    gw_event["httpMethod"] = "GET"

    # THEN it should return 401 without validation error
    result = app(gw_event, {})

    assert result["statusCode"] == 401
    assert result["body"] == "{}"

    # Check execution order - only auth_middleware should have run
    assert execution_log == ["auth_middleware"]


def test_middleware_allows_validation_to_proceed(gw_event):
    """Test that when middleware calls next_middleware, validation still works"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)
    execution_log = []

    def logging_middleware(app, next_middleware):
        execution_log.append("logging_middleware")
        # Log and continue to next middleware
        result = next_middleware(app)
        execution_log.append("logging_middleware_after")
        return result

    app.use(middlewares=[logging_middleware])

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    @app.get("/user")
    def get_user() -> UserModel:
        execution_log.append("route_handler")
        return UserModel(name="Jane", age=25, email="jane@example.com")

    # WHEN calling the user route
    gw_event["path"] = "/user"
    gw_event["httpMethod"] = "GET"

    # THEN it should return 200 with validated response
    result = app(gw_event, {})

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["name"] == "Jane"
    assert response_body["age"] == 25
    assert response_body["email"] == "jane@example.com"

    # Check execution order
    expected_log = ["logging_middleware", "route_handler", "logging_middleware_after"]
    assert execution_log == expected_log


def test_request_validation_fails_before_user_middlewares(gw_event):
    """Test that request validation fails before user middlewares are executed"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)
    execution_log = []

    def passthrough_middleware(app, next_middleware):
        execution_log.append("passthrough_middleware")
        return next_middleware(app)

    app.use(middlewares=[passthrough_middleware])

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    @app.post("/user")
    def create_user(user: UserModel) -> UserModel:
        execution_log.append("route_handler")  # Should not be called due to validation error
        return user

    # WHEN sending invalid request body (missing required fields)
    gw_event["path"] = "/user"
    gw_event["httpMethod"] = "POST"
    gw_event["body"] = '{"name": "John"}'  # Missing age and email
    gw_event["headers"]["Content-Type"] = "application/json"

    # THEN it should return 422 for validation error
    result = app(gw_event, {})

    assert result["statusCode"] == 422
    response_body = json.loads(result["body"])
    assert "detail" in response_body

    # Request validation happens BEFORE user middlewares, so neither should run
    assert "passthrough_middleware" not in execution_log
    assert "route_handler" not in execution_log


def test_request_validation_passes_then_middlewares_execute(gw_event):
    """Test that when request validation passes, user middlewares execute normally"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)
    execution_log = []

    def passthrough_middleware(app, next_middleware):
        execution_log.append("passthrough_middleware")
        return next_middleware(app)

    app.use(middlewares=[passthrough_middleware])

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    @app.post("/user")
    def create_user(user: UserModel) -> UserModel:
        execution_log.append("route_handler")
        return user

    # WHEN sending valid request body
    gw_event["path"] = "/user"
    gw_event["httpMethod"] = "POST"
    gw_event["body"] = '{"name": "John", "age": 30, "email": "john@example.com"}'
    gw_event["headers"]["Content-Type"] = "application/json"

    # THEN it should return 200 and middlewares should execute
    result = app(gw_event, {})

    assert result["statusCode"] == 200

    # Both middleware and route handler should have executed
    assert "passthrough_middleware" in execution_log
    assert "route_handler" in execution_log


def test_multiple_middlewares_with_early_return(gw_event):
    """Test multiple middlewares where one returns early (Issue #4656)"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)
    execution_log = []

    def first_middleware(app, next_middleware):
        execution_log.append("first_middleware")
        return next_middleware(app)

    def auth_middleware(app, next_middleware):
        execution_log.append("auth_middleware")
        # Return early - should not trigger validation
        return Response(status_code=403, content_type="application/json", body="{}")

    def third_middleware(app, next_middleware):
        execution_log.append("third_middleware")  # Should not be called
        return next_middleware(app)

    app.use(middlewares=[first_middleware, auth_middleware, third_middleware])

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    @app.get("/protected")
    def protected_route() -> UserModel:
        execution_log.append("route_handler")  # Should not be called
        return UserModel(name="Secret", age=42, email="secret@example.com")

    # WHEN calling the protected route
    gw_event["path"] = "/protected"
    gw_event["httpMethod"] = "GET"

    # THEN it should return 403 without validation error
    result = app(gw_event, {})

    assert result["statusCode"] == 403
    assert result["body"] == "{}"

    # Check execution order - should stop at auth_middleware
    expected_log = ["first_middleware", "auth_middleware"]
    assert execution_log == expected_log


def test_middleware_execution_order_with_validation(gw_event):
    """Test that middleware execution order is correct with validation enabled"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)
    execution_log = []

    def first_middleware(app, next_middleware):
        execution_log.append("first_middleware")
        return next_middleware(app)

    def second_middleware(app, next_middleware):
        execution_log.append("second_middleware")
        return next_middleware(app)

    app.use(middlewares=[first_middleware, second_middleware])

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    @app.get("/test")
    def test_route() -> UserModel:
        execution_log.append("route_handler")
        return UserModel(name="Test", age=30, email="test@example.com")

    # WHEN calling the test route
    gw_event["path"] = "/test"
    gw_event["httpMethod"] = "GET"

    # THEN it should return 200 with correct execution order
    result = app(gw_event, {})

    assert result["statusCode"] == 200

    # Expected order: first -> second -> route
    expected_order = ["first_middleware", "second_middleware", "route_handler"]
    assert execution_log == expected_order


def test_rate_limiting_middleware_response_not_validated(gw_event):
    """Test rate limiting middleware response (429) is not validated"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    def rate_limit_middleware(app, next_middleware):
        # Return 429 with simple body - should not be validated
        return Response(status_code=429, content_type="application/json", body="{}")

    app.use(middlewares=[rate_limit_middleware])

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    @app.get("/api/data")
    def get_data() -> UserModel:
        return UserModel(name="Data", age=1, email="data@example.com")

    # WHEN calling the rate limited route
    gw_event["path"] = "/api/data"
    gw_event["httpMethod"] = "GET"

    # THEN it should return 429 without validation error
    result = app(gw_event, {})

    assert result["statusCode"] == 429
    assert result["body"] == "{}"


def test_middleware_with_complex_auth_response_gets_validated(gw_event):
    """Test middleware with complex auth response that should be validated"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    def auth_middleware(app, next_middleware):
        # Return complex 401 response - should trigger validation
        return Response(
            status_code=401,
            content_type="application/json",
            body='{"error": "Unauthorized", "message": "Token expired", "code": 1001}',
        )

    app.use(middlewares=[auth_middleware])

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    @app.get("/protected")
    def protected_route() -> UserModel:
        return UserModel(name="Secret", age=42, email="secret@example.com")

    # WHEN calling the protected route
    gw_event["path"] = "/protected"
    gw_event["httpMethod"] = "GET"

    # THEN it should return 401 with complex body (validation should occur)
    result = app(gw_event, {})

    assert result["statusCode"] == 401
    response_body = json.loads(result["body"])
    assert response_body["error"] == "Unauthorized"
    assert response_body["message"] == "Token expired"
    assert response_body["code"] == 1001


def test_normal_route_response_validation_still_works(gw_event):
    """Test that normal route responses are still validated"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    def logging_middleware(app, next_middleware):
        result = next_middleware(app)
        return result

    app.use(middlewares=[logging_middleware])

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    @app.get("/user/<user_id>")
    def get_user(user_id: int) -> UserModel:
        return UserModel(name=f"User{user_id}", age=user_id + 20, email=f"user{user_id}@example.com")

    # WHEN calling the user route
    gw_event["path"] = "/user/123"
    gw_event["httpMethod"] = "GET"

    # THEN it should return 200 with validated response
    result = app(gw_event, {})

    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["name"] == "User123"
    assert response_body["age"] == 143
    assert response_body["email"] == "user123@example.com"


def test_field_discriminator_validation(gw_event):
    """Test that Pydantic Field discriminator works with event_handler validation"""
    app = APIGatewayRestResolver(enable_validation=True)

    class FooAction(BaseModel):
        action: Literal["foo"]
        foo_data: str

    class BarAction(BaseModel):
        action: Literal["bar"]
        bar_data: int

    action_type = Annotated[Union[FooAction, BarAction], Field(discriminator="action")]

    @app.post("/actions")
    def create_action(action: Annotated[action_type, Body()]):
        return {"received_action": action.action, "data": action.model_dump()}

    gw_event["path"] = "/actions"
    gw_event["httpMethod"] = "POST"
    gw_event["headers"]["content-type"] = "application/json"
    gw_event["body"] = '{"action": "foo", "foo_data": "test"}'

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    response_body = json.loads(result["body"])
    assert response_body["received_action"] == "foo"
    assert response_body["data"]["action"] == "foo"
    assert response_body["data"]["foo_data"] == "test"

    gw_event["body"] = '{"action": "bar", "bar_data": 123}'

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    response_body = json.loads(result["body"])
    assert response_body["received_action"] == "bar"
    assert response_body["data"]["action"] == "bar"
    assert response_body["data"]["bar_data"] == 123

    gw_event["body"] = '{"action": "invalid", "some_data": "test"}'

    result = app(gw_event, {})
    assert result["statusCode"] == 422


def test_field_annotation_with_all_param_types(gw_event):
    """A reusable Annotated type carrying a Pydantic Field works with every parameter location."""
    app = APIGatewayRestResolver(enable_validation=True)

    # Reusable annotated type, the same kind you'd use inside a model
    str_field = Annotated[str, Field()]

    @app.get("/header")
    def get_header(h: Annotated[str_field, Header()]):
        return {"value": h}

    @app.get("/path/<p>")
    def get_path(p: Annotated[str_field, Path()]):
        return {"value": p}

    @app.get("/query")
    def get_query(q: Annotated[str_field, Query()]):
        return {"value": q}

    @app.post("/body")
    def post_body(b: Annotated[str_field, Body()]):
        return {"value": b}

    del gw_event["multiValueHeaders"]
    del gw_event["multiValueQueryStringParameters"]

    # Header
    gw_event["path"] = "/header"
    gw_event["httpMethod"] = "GET"
    gw_event["headers"] = {"h": "test"}
    assert app(gw_event, {})["statusCode"] == 200

    # Path
    gw_event["path"] = "/path/test"
    gw_event["pathParameters"] = {"p": "test"}
    assert app(gw_event, {})["statusCode"] == 200

    # Query
    gw_event["path"] = "/query"
    gw_event["pathParameters"] = None
    gw_event["queryStringParameters"] = {"q": "test"}
    assert app(gw_event, {})["statusCode"] == 200

    # Body
    gw_event["path"] = "/body"
    gw_event["httpMethod"] = "POST"
    gw_event["headers"]["content-type"] = "application/json"
    gw_event["body"] = '"test"'
    assert app(gw_event, {})["statusCode"] == 200


def test_field_constraints_apply_with_param_type(gw_event):
    """Constraints declared on a Field are enforced when paired with a location marker."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/items")
    def get_items(quantity: Annotated[int, Field(gt=0), Query()]):
        return {"quantity": quantity}

    gw_event["path"] = "/items"
    gw_event["httpMethod"] = "GET"

    # Passes the gt=0 constraint
    gw_event["queryStringParameters"] = {"quantity": "5"}
    assert app(gw_event, {})["statusCode"] == 200

    # Violates gt=0
    gw_event["queryStringParameters"] = {"quantity": "-1"}
    assert app(gw_event, {})["statusCode"] == 422


def test_validate_pydantic_query_params_with_config_dict_and_validators(gw_event):
    """Test that Pydantic models with ConfigDict, aliases, and validators work correctly"""

    del gw_event["multiValueHeaders"]
    del gw_event["multiValueQueryStringParameters"]

    app = APIGatewayRestResolver(enable_validation=True)

    def _validate_powertools(value: str) -> str:
        if not value.startswith("Powertools"):
            raise ValueError("Full name must start with 'Powertools'")
        return value

    class QuerySimple(BaseModel):
        full_name: Annotated[str, StringConstraints(min_length=5), AfterValidator(_validate_powertools)]
        next_token: Base64UrlStr
        search_id: str

    @app.get("/query-model-simple")
    def query_model(params: Annotated[QuerySimple, Query()]) -> Dict[str, Any]:
        return {
            "fullName": params.full_name,
            "nextToken": params.next_token,
            "searchId": params.search_id,
        }

    class QueryAdvanced(BaseModel):
        full_name: Annotated[str, StringConstraints(min_length=5)]
        next_token: str
        search_id: Annotated[str, Field(alias="id")]  # Using str instead of UUID4 for simpler testing

        model_config = ConfigDict(
            alias_generator=alias_generators.to_camel,
            validate_by_alias=True,
            validate_by_name=True,
            serialize_by_alias=True,
        )

    @app.get("/query-model-advanced")
    def query_model_advanced(params: Annotated[QueryAdvanced, Query()]) -> Dict[str, Any]:
        return params.model_dump()

    # Test QuerySimple with validators
    gw_event["path"] = "/query-model-simple"
    gw_event["queryStringParameters"] = {
        "full_name": "Powertools Lambda",
        "next_token": "dGVzdA==",  # base64url encoded "test"
        "search_id": "search-123",
    }

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["fullName"] == "Powertools Lambda"
    assert body["nextToken"] == "test"
    assert body["searchId"] == "search-123"

    # Test QuerySimple validation error (name doesn't start with "Powertools")
    gw_event["queryStringParameters"] = {
        "full_name": "Lambda Powertools",
        "next_token": "dGVzdA==",
        "search_id": "search-123",
    }

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    errors = body["detail"]

    # Should have validation error for full_name with proper location
    full_name_error = next((e for e in errors if "full_name" in e["loc"]), None)

    assert full_name_error is not None, "Should have error for full_name field"

    # Check error details for full_name
    assert full_name_error["loc"] == ["query", "params", "full_name"]
    assert full_name_error["type"] == "value_error"

    # Test QueryAdvanced with ConfigDict and alias_generator
    gw_event["path"] = "/query-model-advanced"
    gw_event["queryStringParameters"] = {
        "fullName": "Advanced Test",  # camelCase from alias_generator
        "nextToken": "dGVzdA==",  # camelCase from alias_generator
        "id": "search-456",  # explicit alias
    }

    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    # Should return with camelCase keys due to serialize_by_alias=True
    assert body["fullName"] == "Advanced Test"
    assert body["nextToken"] == "dGVzdA=="
    assert body["id"] == "search-456"

    # Test QueryAdvanced with snake_case field names due to validate_by_name=True
    gw_event["queryStringParameters"] = {
        "full_name": "Snake Case Test",  # snake_case field name
        "next_token": "dGVzdA==",  # snake_case field name
        "search_id": "search-789",  # snake_case field name
    }

    gw_event["path"] = "/query-model-advanced"
    result = app(gw_event, {})
    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["fullName"] == "Snake Case Test"
    assert body["nextToken"] == "dGVzdA=="
    assert body["id"] == "search-789"

    # Test QueryAdvanced validation error (full_name too short)
    gw_event["queryStringParameters"] = {
        "fullName": "Bad",  # Too short (min_length=5)
        "nextToken": "dGVzdA==",
        "id": "search-456",
    }

    result = app(gw_event, {})
    assert result["statusCode"] == 422

    body = json.loads(result["body"])
    assert "detail" in body
    errors = body["detail"]

    # Should have validation error for full_name with proper location
    full_name_error = next((e for e in errors if "full_name" in e["loc"] or "fullName" in e["loc"]), None)
    assert full_name_error is not None
    assert full_name_error["type"] == "string_too_short"


def test_validation_query_string_with_fully_encoded_datetime_alb_resolver():
    # GIVEN a ALBResolver with validation enabled,
    # and an event with a fully url-encoded datetime
    # as a query string parameter
    app = ALBResolver(enable_validation=True, decode_query_parameters=True)
    raw_event = load_event("albEvent.json")
    raw_event["path"] = "/users"
    # Fully encoded: "2025-12-20T16:56:02.032000" -> "2025-12-20T16%3A56%3A02.032000"
    # With spaces or special chars: "2025-12-20 16:56:02" -> "2025-12-20%2016%3A56%3A02"
    raw_event["queryStringParameters"] = {"query_dt": "2025-12-20T16%3A56%3A02.032000"}

    @app.get("/users")
    def handler(query_dt: datetime.datetime):
        return {"received": query_dt.isoformat()}

    result = app(raw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["received"] == "2025-12-20T16:56:02.032000"


def test_validation_query_string_with_encoded_key_and_value_alb_resolver():
    # GIVEN a ALBResolver with validation enabled,
    # and an event with url-encoded key AND value
    app = ALBResolver(enable_validation=True, decode_query_parameters=True)
    raw_event = load_event("albEvent.json")
    raw_event["path"] = "/search"
    # Key: "search query" -> "search%20query"
    # Value: "hello world" -> "hello%20world"
    raw_event["queryStringParameters"] = {"search%20query": "hello%20world"}

    @app.get("/search")
    def handler(search_query: Annotated[str, Query(alias="search query")]):
        return {"result": search_query}

    result = app(raw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["result"] == "hello world"


def test_validation_without_decode_query_parameters_alb_resolver():
    # GIVEN a ALBResolver WITHOUT decode_query_parameters (default behavior)
    app = ALBResolver(enable_validation=True)
    raw_event = load_event("albEvent.json")
    raw_event["path"] = "/users"
    raw_event["queryStringParameters"] = {"query_dt": "2025-12-20T16%3A56%3A02.032000"}

    @app.get("/users")
    def handler(query_dt: datetime.datetime):
        return None

    # THEN validation should fail because the encoded string is not a valid datetime
    result = app(raw_event, {})
    assert result["statusCode"] == 422


def test_validate_union_single_or_list_body_with_list(gw_event):
    """Test that Union[Model, List[Model]] correctly handles a list of items"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Item(BaseModel):
        name: str
        value: int

    # WHEN a handler is defined with Union[Model, List[Model]] body parameter
    @app.post("/items")
    def handler(items: Annotated[Union[Item, List[Item]], Body()]) -> Dict[str, Any]:
        # Should receive the full list, not just the first element
        if isinstance(items, list):
            return {"count": len(items), "items": [item.model_dump() for item in items]}
        else:
            return {"count": 1, "items": [items.model_dump()]}

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/items"
    # Send a list of items
    gw_event["body"] = json.dumps(
        [
            {"name": "item1", "value": 10},
            {"name": "item2", "value": 20},
            {"name": "item3", "value": 30},
        ],
    )

    # THEN the handler should receive all items in the list, not just the first one
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["count"] == 3
    assert len(body["items"]) == 3
    assert body["items"][0]["name"] == "item1"
    assert body["items"][1]["name"] == "item2"
    assert body["items"][2]["name"] == "item3"


def test_validate_union_single_or_list_body_with_single(gw_event):
    """Test that Union[Model, List[Model]] correctly handles a single item"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Item(BaseModel):
        name: str
        value: int

    # WHEN a handler is defined with Union[Model, List[Model]] body parameter
    @app.post("/items")
    def handler(items: Annotated[Union[Item, List[Item]], Body()]) -> Dict[str, Any]:
        if isinstance(items, list):
            return {"count": len(items), "items": [item.model_dump() for item in items]}
        else:
            return {"count": 1, "items": [items.model_dump()]}

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/items"
    # Send a single item
    gw_event["body"] = json.dumps({"name": "single_item", "value": 42})

    # THEN the handler should receive the single item
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["count"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "single_item"
    assert body["items"][0]["value"] == 42


def test_validate_rootmodel_list_body(gw_event):
    """Test that RootModel[List[Model]] correctly handles a list of items"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Item(BaseModel):
        name: str
        value: int

    class ItemCollection(RootModel[List[Item]]):
        root: List[Item]

    # WHEN a handler is defined with RootModel[List[Model]] body parameter
    @app.post("/items")
    def handler(collection: Annotated[ItemCollection, Body()]) -> Dict[str, Any]:
        # collection.root should contain the full list
        items = collection.root
        return {"count": len(items), "items": [item.model_dump() for item in items]}

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/items"
    # Send a list of items
    gw_event["body"] = json.dumps(
        [
            {"name": "item1", "value": 100},
            {"name": "item2", "value": 200},
        ],
    )

    # THEN the handler should receive all items in the collection
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["count"] == 2
    assert len(body["items"]) == 2
    assert body["items"][0]["name"] == "item1"
    assert body["items"][0]["value"] == 100
    assert body["items"][1]["name"] == "item2"
    assert body["items"][1]["value"] == 200


def test_validate_nested_union_with_sequence(gw_event):
    """Test that nested Union types containing sequences are handled correctly"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Person(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a complex Union including List
    @app.post("/people")
    def handler(
        data: Annotated[Union[str, List[Person], Person], Body()],
    ) -> Dict[str, Any]:
        if isinstance(data, str):
            return {"type": "string", "value": data}
        elif isinstance(data, list):
            return {"type": "list", "count": len(data)}
        else:
            return {"type": "person", "name": data.name}

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/people"
    # Send a list
    gw_event["body"] = json.dumps(
        [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ],
    )

    # THEN the handler should receive the full list
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["type"] == "list"
    assert body["count"] == 2


# ────────────────────────────────────────────────────────────────────
# Regression tests for Union / RootModel / Optional sequence body
# See: https://github.com/aws-powertools/powertools-lambda-python/issues/8057
# ────────────────────────────────────────────────────────────────────


class _Item(BaseModel):
    name: str
    value: int


class _ItemCollection(RootModel[List[_Item]]):
    pass


_THREE_ITEMS = [
    {"name": "a", "value": 1},
    {"name": "b", "value": 2},
    {"name": "c", "value": 3},
]


def _post_json(app, path, payload):
    """Helper: build a minimal APIGW REST event, POST JSON, return parsed result."""
    from tests.functional.utils import load_event

    event = load_event("apiGatewayProxyEvent.json")
    event["httpMethod"] = "POST"
    event["path"] = path
    event["body"] = json.dumps(payload)
    result = app(event, {})
    return result["statusCode"], json.loads(result["body"])


# ---------- Optional[List[Model]] ----------


def test_optional_list_body_with_list():
    """Optional[List[Model]] must preserve the full list."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[Optional[List[_Item]], Body()]) -> Dict[str, Any]:
        assert isinstance(items, list)
        return {"count": len(items)}

    status, body = _post_json(app, "/items", _THREE_ITEMS)
    assert status == 200
    assert body["count"] == 3


def test_optional_list_body_with_none():
    """Optional[List[Model]] must accept a null body gracefully."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[Optional[List[_Item]], Body()] = None) -> Dict[str, Any]:
        return {"received_none": items is None}

    status, body = _post_json(app, "/items", None)
    assert status == 200
    assert body["received_none"] is True


# ---------- Optional[Union[Model, List[Model]]] ----------


def test_optional_union_model_or_list_with_list():
    """Optional[Union[Model, List[Model]]] — send list, get full list."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[Optional[Union[_Item, List[_Item]]], Body()]) -> Dict[str, Any]:
        assert isinstance(items, list)
        return {"count": len(items)}

    status, body = _post_json(app, "/items", _THREE_ITEMS)
    assert status == 200
    assert body["count"] == 3


def test_optional_union_model_or_list_with_single():
    """Optional[Union[Model, List[Model]]] — send single obj, get single obj."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[Optional[Union[_Item, List[_Item]]], Body()]) -> Dict[str, Any]:
        assert not isinstance(items, list)
        return {"name": items.name}

    status, body = _post_json(app, "/items", {"name": "solo", "value": 99})
    assert status == 200
    assert body["name"] == "solo"


def test_optional_union_model_or_list_with_none():
    """Optional[Union[Model, List[Model]]] — send null, get None."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[Optional[Union[_Item, List[_Item]]], Body()] = None) -> Dict[str, Any]:
        return {"is_none": items is None}

    status, body = _post_json(app, "/items", None)
    assert status == 200
    assert body["is_none"] is True


# ---------- List[Model] directly (no Union / Optional) ----------


def test_plain_list_body_preserves_all_items():
    """List[Model] — baseline: must never truncate."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[List[_Item], Body()]) -> Dict[str, Any]:
        return {"count": len(items)}

    status, body = _post_json(app, "/items", _THREE_ITEMS)
    assert status == 200
    assert body["count"] == 3


# ---------- Empty list ----------


def test_union_model_or_list_with_empty_list():
    """Union[Model, List[Model]] with [] — must not crash on value[0]."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[Union[_Item, List[_Item]], Body()]) -> Dict[str, Any]:
        if isinstance(items, list):
            return {"count": len(items)}
        return {"count": 1}

    status, body = _post_json(app, "/items", [])
    assert status == 200
    assert body["count"] == 0


def test_plain_list_with_empty_list():
    """List[Model] with [] — must accept empty list."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[List[_Item], Body()]) -> Dict[str, Any]:
        return {"count": len(items)}

    status, body = _post_json(app, "/items", [])
    assert status == 200
    assert body["count"] == 0


# ---------- Single-element list (boundary) ----------


def test_union_model_or_list_with_single_element_list():
    """Union[Model, List[Model]] with [single_item] — must NOT unwrap to scalar."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[Union[_Item, List[_Item]], Body()]) -> Dict[str, Any]:
        if isinstance(items, list):
            return {"type": "list", "count": len(items)}
        return {"type": "single"}

    status, body = _post_json(app, "/items", [{"name": "only", "value": 1}])
    assert status == 200
    # Pydantic may match as single Item or list — either is valid,
    # but it must NOT crash or lose data
    assert body.get("count", 1) == 1


# ---------- Union with primitive sequences ----------


def test_union_str_or_list_dict():
    """Union[str, List[dict]] — list of dicts must arrive intact."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/data")
    def handler(data: Annotated[Union[str, List[Dict[str, Any]]], Body()]) -> Dict[str, Any]:
        if isinstance(data, list):
            return {"type": "list", "count": len(data)}
        return {"type": "str"}

    payload = [{"key": "v1"}, {"key": "v2"}]
    status, body = _post_json(app, "/data", payload)
    assert status == 200
    assert body["type"] == "list"
    assert body["count"] == 2


# ---------- RootModel edge cases ----------


def test_optional_rootmodel_list_body():
    """Optional[RootModel[List[Model]]] — list must not be truncated."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[Optional[_ItemCollection], Body()]) -> Dict[str, Any]:
        return {"count": len(items.root)}

    status, body = _post_json(app, "/items", _THREE_ITEMS)
    assert status == 200
    assert body["count"] == 3


def test_union_rootmodel_and_model():
    """Union[RootModel[List[Model]], Model] — list must not be truncated."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[Union[_ItemCollection, _Item], Body()]) -> Dict[str, Any]:
        if isinstance(items, _ItemCollection):
            return {"type": "collection", "count": len(items.root)}
        return {"type": "single", "name": items.name}

    status, body = _post_json(app, "/items", _THREE_ITEMS)
    assert status == 200
    assert body["type"] == "collection"
    assert body["count"] == 3


# ---------- Python 3.10+ pipe Union syntax ----------


def test_pipe_union_syntax_model_or_list():
    """Model | List[Model] (PEP 604 syntax) — list must not be truncated."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[_Item | List[_Item], Body()]) -> Dict[str, Any]:  # noqa: FA102
        if isinstance(items, list):
            return {"count": len(items)}
        return {"count": 1}

    status, body = _post_json(app, "/items", _THREE_ITEMS)
    assert status == 200
    assert body["count"] == 3


def test_pipe_union_optional_list():
    """List[Model] | None (PEP 604 Optional) — list must not be truncated."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[List[_Item] | None, Body()]) -> Dict[str, Any]:  # noqa: FA102
        if items is None:
            return {"count": 0}
        return {"count": len(items)}

    status, body = _post_json(app, "/items", _THREE_ITEMS)
    assert status == 200
    assert body["count"] == 3


# ---------- Deeply nested: RootModel[Union[Model, List[Model]]] ----------


def test_rootmodel_wrapping_union_with_sequence():
    """RootModel[Union[Model, List[Model]]] — inner Union sequence must be detected."""
    app = APIGatewayRestResolver(enable_validation=True)

    class FlexiblePayload(RootModel[Union[_Item, List[_Item]]]):
        pass

    @app.post("/items")
    def handler(payload: Annotated[FlexiblePayload, Body()]) -> Dict[str, Any]:
        data = payload.root
        if isinstance(data, list):
            return {"type": "list", "count": len(data)}
        return {"type": "single", "name": data.name}

    status, body = _post_json(app, "/items", _THREE_ITEMS)
    assert status == 200
    assert body["type"] == "list"
    assert body["count"] == 3


# ---------- Multiple resolvers (ALB, HTTP API, etc.) ----------


def test_union_list_body_works_across_resolvers():
    """Regression: ensure fix works for ALB and HTTP API resolvers too."""
    for ResolverClass in [APIGatewayHttpResolver, ALBResolver]:
        app = ResolverClass(enable_validation=True)

        @app.post("/items")
        def handler(items: Annotated[Union[_Item, List[_Item]], Body()]) -> Dict[str, Any]:
            if isinstance(items, list):
                return {"count": len(items)}
            return {"count": 1}

        # Build event appropriate for resolver
        if ResolverClass is APIGatewayHttpResolver:
            event = load_event("apiGatewayProxyV2Event.json")
            event["requestContext"]["http"]["method"] = "POST"
            event["requestContext"]["http"]["path"] = "/items"
            event["rawPath"] = "/items"
        else:
            event = load_event("albEvent.json")
            event["httpMethod"] = "POST"
            event["path"] = "/items"

        event["body"] = json.dumps(_THREE_ITEMS)
        result = app(event, {})
        assert result["statusCode"] == 200
        body_result = json.loads(result["body"])
        assert body_result["count"] == 3, f"Failed for {ResolverClass.__name__}"


# ---------- Large list (stress boundary) ----------


def test_union_list_body_large_payload():
    """Union[Model, List[Model]] with 100 items — no truncation."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def handler(items: Annotated[Union[_Item, List[_Item]], Body()]) -> Dict[str, Any]:
        assert isinstance(items, list)
        return {"count": len(items)}

    big_payload = [{"name": f"item-{i}", "value": i} for i in range(100)]
    status, body = _post_json(app, "/items", big_payload)
    assert status == 200
    assert body["count"] == 100


# ---------- File upload (multipart/form-data) ----------


def _build_multipart_body(fields: List[Dict], boundary: str = "----TestBoundary") -> Tuple[str, str]:
    """
    Build a multipart/form-data body and return (base64_body, content_type).

    Each field dict can have:
      - name: field name (required)
      - value: str or bytes (required)
      - filename: optional filename (makes it a file part)
      - content_type: optional content type for the part
    """
    parts = []
    for field in fields:
        headers = f'Content-Disposition: form-data; name="{field["name"]}"'
        if "filename" in field:
            headers += f'; filename="{field["filename"]}"'
        if "content_type" in field:
            headers += f"\r\nContent-Type: {field['content_type']}"
        value = field["value"]
        if isinstance(value, str):
            value = value.encode("utf-8")
        parts.append((headers, value))

    body = b""
    for headers, value in parts:
        body += f"--{boundary}\r\n".encode()
        body += f"{headers}\r\n\r\n".encode()
        body += value
        body += b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    content_type = f"multipart/form-data; boundary={boundary}"
    return base64.b64encode(body).decode("utf-8"), content_type


def test_file_upload_basic(gw_event):
    """Test basic file upload with File() parameter."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[bytes, File()]):
        return {"size": len(file_data)}

    body, content_type = _build_multipart_body(
        [
            {"name": "file_data", "value": b"hello world", "filename": "test.txt"},
        ],
    )

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = content_type
    gw_event["body"] = body
    gw_event["isBase64Encoded"] = True

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"size": 11}


def test_file_upload_with_form_field(gw_event):
    """Test file upload mixed with a regular form field."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(
        description: Annotated[str, Form()],
        file_data: Annotated[bytes, File()],
    ):
        return {"description": description, "size": len(file_data)}

    body, content_type = _build_multipart_body(
        [
            {"name": "description", "value": "my file"},
            {"name": "file_data", "value": b"\x89PNG\r\n\x1a\n", "filename": "image.png", "content_type": "image/png"},
        ],
    )

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = content_type
    gw_event["body"] = body
    gw_event["isBase64Encoded"] = True

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    parsed = json.loads(result["body"])
    assert parsed["description"] == "my file"
    assert parsed["size"] == 8


def test_file_upload_missing_required(gw_event):
    """Test that missing required File() parameter returns 422."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[bytes, File()]):
        return {"size": len(file_data)}

    # Send empty multipart body (no file_data field)
    body, content_type = _build_multipart_body(
        [
            {"name": "other_field", "value": "some value"},
        ],
    )

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = content_type
    gw_event["body"] = body
    gw_event["isBase64Encoded"] = True

    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


def test_file_upload_openapi_schema():
    """Test that File() parameters generate correct OpenAPI schema."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[bytes, File(description="The file to upload")]):
        return {"size": len(file_data)}

    schema = app.get_openapi_schema()
    path = schema.paths["/upload"]
    post_op = path.post

    # Should have a request body with multipart/form-data
    assert post_op.requestBody is not None
    content = post_op.requestBody.content
    assert "multipart/form-data" in content

    # The schema should reference a binary format field
    multipart_schema = content["multipart/form-data"].schema_
    assert multipart_schema is not None


def test_file_upload_non_base64(gw_event):
    """Test file upload when body is not base64-encoded (edge case)."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[bytes, File()]):
        return {"size": len(file_data)}

    # Build multipart body without base64 encoding
    boundary = "----TestBoundary"
    raw_body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file_data"; filename="test.txt"\r\n'
        f"\r\n"
        f"hello world\r\n"
        f"--{boundary}--\r\n"
    )

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = f"multipart/form-data; boundary={boundary}"
    gw_event["body"] = raw_body
    gw_event["isBase64Encoded"] = False

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"size": 11}


def test_file_upload_non_base64_emits_warning(gw_event):
    """Test that non-base64 multipart body emits a warning about API Gateway config."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[bytes, File()]):
        return {"size": len(file_data)}

    boundary = "----TestBoundary"
    raw_body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file_data"; filename="test.txt"\r\n'
        f"\r\n"
        f"hello world\r\n"
        f"--{boundary}--\r\n"
    )

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = f"multipart/form-data; boundary={boundary}"
    gw_event["body"] = raw_body
    gw_event["isBase64Encoded"] = False

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = app(gw_event, {})

    assert result["statusCode"] == 200
    assert len(w) == 1
    assert "Binary Media Types" in str(w[0].message)


def test_file_upload_non_base64_binary_content(gw_event):
    """Test file upload with raw binary bytes (e.g. JPEG) without base64 encoding."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[bytes, File()]):
        return {"size": len(file_data)}

    # Simulate binary content with bytes that are NOT valid UTF-8 (like JPEG header 0xFF 0xD8)
    binary_content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00"
    boundary = "----TestBoundary"
    raw_bytes = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file_data"; filename="photo.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n"
            f"\r\n"
        ).encode("latin-1")
        + binary_content
        + f"\r\n--{boundary}--\r\n".encode("latin-1")
    )

    # Without binary mode, API Gateway passes body as latin-1 compatible string
    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = f"multipart/form-data; boundary={boundary}"
    gw_event["body"] = raw_bytes.decode("latin-1")
    gw_event["isBase64Encoded"] = False

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        result = app(gw_event, {})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"size": len(binary_content)}


def test_upload_file_with_metadata(gw_event):
    """Test UploadFile annotation provides filename and content_type."""
    from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[UploadFile, File()]):
        return {
            "filename": file_data.filename,
            "content_type": file_data.content_type,
            "size": len(file_data),
        }

    body, content_type = _build_multipart_body(
        [
            {"name": "file_data", "value": b"fake jpeg", "filename": "photo.jpg", "content_type": "image/jpeg"},
        ],
    )

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = content_type
    gw_event["body"] = body
    gw_event["isBase64Encoded"] = True

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    parsed = json.loads(result["body"])
    assert parsed["filename"] == "photo.jpg"
    assert parsed["content_type"] == "image/jpeg"
    assert parsed["size"] == 9


def test_upload_file_mixed_with_form(gw_event):
    """Test UploadFile + Form fields together."""
    from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(
        file_data: Annotated[UploadFile, File()],
        title: Annotated[str, Form()],
    ):
        return {
            "title": title,
            "filename": file_data.filename,
            "size": len(file_data),
        }

    body, content_type = _build_multipart_body(
        [
            {"name": "title", "value": "My Document"},
            {
                "name": "file_data",
                "value": b"pdf content here",
                "filename": "doc.pdf",
                "content_type": "application/pdf",
            },
        ],
    )

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = content_type
    gw_event["body"] = body
    gw_event["isBase64Encoded"] = True

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    parsed = json.loads(result["body"])
    assert parsed["title"] == "My Document"
    assert parsed["filename"] == "doc.pdf"
    assert parsed["size"] == 16


def test_upload_file_openapi_schema():
    """Test UploadFile generates correct OpenAPI schema."""
    from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[UploadFile, File(description="A file")]):
        return {}

    schema = app.get_openapi_schema()
    schema_dict = schema.model_dump(exclude_none=True, by_alias=True)
    upload_path = schema_dict["paths"]["/upload"]["post"]
    content = upload_path["requestBody"]["content"]
    assert "multipart/form-data" in content

    # Resolve $ref to get the actual schema
    ref = content["multipart/form-data"]["schema"]["$ref"]
    schema_name = ref.split("/")[-1]
    props = schema_dict["components"]["schemas"][schema_name]["properties"]
    assert props["file_data"]["type"] == "string"
    assert props["file_data"]["format"] == "binary"


def test_multipart_missing_boundary(gw_event):
    """Test that missing boundary in content-type raises ValueError."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[bytes, File()]):
        return {"size": len(file_data)}

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = "multipart/form-data"  # no boundary
    gw_event["body"] = base64.b64encode(b"some data").decode()
    gw_event["isBase64Encoded"] = True

    with pytest.raises(ValueError, match="Missing boundary"):
        app(gw_event, {})


def test_multipart_quoted_boundary(gw_event):
    """Test that boundary with quotes is parsed correctly."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[bytes, File()]):
        return {"size": len(file_data)}

    boundary = "----TestBoundary"
    body, _ = _build_multipart_body(
        [
            {"name": "file_data", "value": b"hello", "filename": "test.txt"},
        ],
        boundary=boundary,
    )

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    # Use quoted boundary
    gw_event["headers"]["content-type"] = f'multipart/form-data; boundary="{boundary}"'
    gw_event["body"] = body
    gw_event["isBase64Encoded"] = True

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"size": 5}


def test_multipart_multiple_values_same_field(gw_event):
    """Test multiple values for the same field name are collected as list."""
    from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[List[UploadFile], File()]):
        return {"count": len(file_data), "filenames": [f.filename for f in file_data]}

    # Build body with two parts having the same field name
    boundary = "----TestBoundary"
    raw = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file_data"; filename="a.txt"\r\n'
        f"\r\n"
        f"content a\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file_data"; filename="b.txt"\r\n'
        f"\r\n"
        f"content b\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = f"multipart/form-data; boundary={boundary}"
    gw_event["body"] = base64.b64encode(raw).decode()
    gw_event["isBase64Encoded"] = True

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    parsed = json.loads(result["body"])
    assert parsed["count"] == 2
    assert parsed["filenames"] == ["a.txt", "b.txt"]


def test_multipart_three_values_same_field(gw_event):
    """Test three or more values for same field name builds onto existing list."""
    from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[List[UploadFile], File()]):
        return {"count": len(file_data), "filenames": [f.filename for f in file_data]}

    boundary = "----TestBoundary"
    raw = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file_data"; filename="a.txt"\r\n'
        f"\r\n"
        f"aaa\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file_data"; filename="b.txt"\r\n'
        f"\r\n"
        f"bbb\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file_data"; filename="c.txt"\r\n'
        f"\r\n"
        f"ccc\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = f"multipart/form-data; boundary={boundary}"
    gw_event["body"] = base64.b64encode(raw).decode()
    gw_event["isBase64Encoded"] = True

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    parsed = json.loads(result["body"])
    assert parsed["count"] == 3
    assert parsed["filenames"] == ["a.txt", "b.txt", "c.txt"]


def test_multipart_part_without_headers_separator(gw_event):
    """Test that a malformed part missing the header/body separator is skipped."""
    from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[UploadFile, File()]):
        return {"filename": file_data.filename}

    # Build a body with one malformed part (no \r\n\r\n) and one valid part
    boundary = "----TestBoundary"
    raw = (
        f"--{boundary}\r\n"
        f"This part has no header separator at all\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file_data"; filename="good.txt"\r\n'
        f"\r\n"
        f"good content\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = f"multipart/form-data; boundary={boundary}"
    gw_event["body"] = base64.b64encode(raw).decode()
    gw_event["isBase64Encoded"] = True

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    parsed = json.loads(result["body"])
    assert parsed["filename"] == "good.txt"


def test_multipart_part_without_field_name(gw_event):
    """Test that a part missing the name parameter in Content-Disposition is skipped."""
    from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[UploadFile, File()]):
        return {"filename": file_data.filename}

    # Build a body with one part that has no name= param and one valid part
    boundary = "----TestBoundary"
    raw = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data\r\n"
        f"\r\n"
        f"orphan content\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file_data"; filename="valid.txt"\r\n'
        f"\r\n"
        f"valid content\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = f"multipart/form-data; boundary={boundary}"
    gw_event["body"] = base64.b64encode(raw).decode()
    gw_event["isBase64Encoded"] = True

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    parsed = json.loads(result["body"])
    assert parsed["filename"] == "valid.txt"


def test_upload_file_validate_error():
    """Test UploadFile._validate raises ValueError for non-UploadFile values."""
    from aws_lambda_powertools.event_handler.openapi.params import UploadFile

    with pytest.raises(ValueError, match="Expected UploadFile, got str"):
        UploadFile._validate("not an upload file")

    with pytest.raises(ValueError, match="Expected UploadFile, got int"):
        UploadFile._validate(42)


def test_multipart_unclosed_quote_in_header():
    """Test that _extract_header_param returns None when quote is unclosed."""
    from aws_lambda_powertools.event_handler.middlewares.openapi_validation import _extract_header_param

    # name=" is present but closing quote is missing
    result = _extract_header_param('Content-Disposition: form-data; name="broken', "name")
    assert result is None


def test_multipart_generic_parse_error(gw_event):
    """Test that non-ValueError exceptions during multipart parsing produce 422."""
    from unittest.mock import patch

    from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload(file_data: Annotated[UploadFile, File()]):
        return {"filename": file_data.filename}

    body_b64, content_type = _build_multipart_body(
        [{"name": "file_data", "value": b"data", "filename": "test.txt"}],
    )

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/upload"
    gw_event["headers"]["content-type"] = content_type
    gw_event["body"] = body_b64
    gw_event["isBase64Encoded"] = True

    # Patch _parse_multipart_body to raise a non-ValueError (e.g. TypeError)
    with patch(
        "aws_lambda_powertools.event_handler.middlewares.openapi_validation._parse_multipart_body",
        side_effect=TypeError("unexpected type"),
    ):
        result = app(gw_event, {})
        assert result["statusCode"] == 422
        body = json.loads(result["body"])
        assert body["detail"][0]["type"] == "multipart_invalid"


# ---------- Cookie parameter tests ----------


def test_cookie_param_basic(gw_event):
    """Test basic cookie parameter extraction from REST API v1 (Cookie header)."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/me")
    def handler(session_id: Annotated[str, Cookie()]):
        return {"session_id": session_id}

    gw_event["path"] = "/me"
    gw_event["headers"]["cookie"] = "session_id=abc123; theme=dark"
    # Clear multiValueHeaders to avoid interference
    gw_event.pop("multiValueHeaders", None)

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["session_id"] == "abc123"


def test_cookie_param_missing_required(gw_event):
    """Test that a missing required cookie returns 422."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/me")
    def handler(session_id: Annotated[str, Cookie()]):
        return {"session_id": session_id}

    gw_event["path"] = "/me"
    gw_event["headers"]["cookie"] = "theme=dark"
    gw_event.pop("multiValueHeaders", None)

    result = app(gw_event, {})
    assert result["statusCode"] == 422


def test_cookie_param_with_default(gw_event):
    """Test cookie parameter with a default value when cookie is absent."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/me")
    def handler(theme: Annotated[str, Cookie()] = "light"):
        return {"theme": theme}

    gw_event["path"] = "/me"
    gw_event["headers"].pop("cookie", None)
    gw_event.pop("multiValueHeaders", None)

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["theme"] == "light"


def test_cookie_param_multiple_cookies(gw_event):
    """Test extracting multiple cookie parameters."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/me")
    def handler(
        session_id: Annotated[str, Cookie()],
        theme: Annotated[str, Cookie()] = "light",
    ):
        return {"session_id": session_id, "theme": theme}

    gw_event["path"] = "/me"
    gw_event["headers"]["cookie"] = "session_id=abc123; theme=dark"
    gw_event.pop("multiValueHeaders", None)

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["session_id"] == "abc123"
    assert body["theme"] == "dark"


def test_cookie_param_int_validation(gw_event):
    """Test cookie parameter with int type validation."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/me")
    def handler(visits: Annotated[int, Cookie()]):
        return {"visits": visits}

    gw_event["path"] = "/me"
    gw_event["headers"]["cookie"] = "visits=42"
    gw_event.pop("multiValueHeaders", None)

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["visits"] == 42

    # Invalid int
    gw_event["headers"]["cookie"] = "visits=not_a_number"
    result = app(gw_event, {})
    assert result["statusCode"] == 422


def test_cookie_param_http_api_v2(gw_event_http):
    """Test cookie parameter with HTTP API v2 (dedicated cookies field)."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = APIGatewayHttpResolver(enable_validation=True)

    @app.get("/me")
    def handler(session_id: Annotated[str, Cookie()]):
        return {"session_id": session_id}

    gw_event_http["rawPath"] = "/me"
    gw_event_http["requestContext"]["http"]["method"] = "GET"
    gw_event_http["cookies"] = ["session_id=xyz789", "theme=dark"]

    result = app(gw_event_http, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["session_id"] == "xyz789"


def test_cookie_param_lambda_function_url(gw_event_lambda_url):
    """Test cookie parameter with Lambda Function URL (v2 format)."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = LambdaFunctionUrlResolver(enable_validation=True)

    @app.get("/me")
    def handler(session_id: Annotated[str, Cookie()]):
        return {"session_id": session_id}

    gw_event_lambda_url["rawPath"] = "/me"
    gw_event_lambda_url["requestContext"]["http"]["method"] = "GET"
    gw_event_lambda_url["cookies"] = ["session_id=fn_url_abc"]

    result = app(gw_event_lambda_url, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["session_id"] == "fn_url_abc"


def test_cookie_param_alb(gw_event_alb):
    """Test cookie parameter with ALB (Cookie header in multiValueHeaders)."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = ALBResolver(enable_validation=True)

    @app.get("/me")
    def handler(session_id: Annotated[str, Cookie()]):
        return {"session_id": session_id}

    gw_event_alb["path"] = "/me"
    gw_event_alb["httpMethod"] = "GET"
    gw_event_alb["multiValueHeaders"]["cookie"] = ["session_id=alb_abc"]

    result = app(gw_event_alb, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["session_id"] == "alb_abc"


def test_cookie_param_openapi_schema():
    """Test that Cookie() generates correct OpenAPI schema with in=cookie."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/me")
    def handler(
        session_id: Annotated[str, Cookie(description="Session identifier")],
        theme: Annotated[str, Cookie(description="UI theme")] = "light",
    ):
        return {"session_id": session_id}

    schema = app.get_openapi_schema()
    schema_dict = schema.model_dump(mode="json", by_alias=True, exclude_none=True)

    path = schema_dict["paths"]["/me"]["get"]
    params = path["parameters"]

    cookie_params = [p for p in params if p["in"] == "cookie"]
    assert len(cookie_params) == 2

    session_param = next(p for p in cookie_params if p["name"] == "session_id")
    assert session_param["required"] is True
    assert session_param["description"] == "Session identifier"

    theme_param = next(p for p in cookie_params if p["name"] == "theme")
    assert theme_param.get("required") is not True
    assert theme_param["description"] == "UI theme"


def test_cookie_param_with_query_and_header(gw_event):
    """Test that Cookie(), Query(), and Header() work together."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/me")
    def handler(
        user_id: Annotated[str, Query()],
        x_request_id: Annotated[str, Header()],
        session_id: Annotated[str, Cookie()],
    ):
        return {
            "user_id": user_id,
            "x_request_id": x_request_id,
            "session_id": session_id,
        }

    gw_event["path"] = "/me"
    gw_event["queryStringParameters"] = {"user_id": "u123"}
    gw_event["multiValueQueryStringParameters"] = {"user_id": ["u123"]}
    gw_event["headers"]["x-request-id"] = "req-456"
    gw_event["multiValueHeaders"] = {"x-request-id": ["req-456"], "cookie": ["session_id=sess-789"]}
    gw_event["headers"]["cookie"] = "session_id=sess-789"

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["user_id"] == "u123"
    assert body["x_request_id"] == "req-456"
    assert body["session_id"] == "sess-789"


def test_cookie_param_no_cookies_in_request(gw_event):
    """Test that empty cookies dict is handled gracefully."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/me")
    def handler(theme: Annotated[str, Cookie()] = "light"):
        return {"theme": theme}

    gw_event["path"] = "/me"
    gw_event["headers"] = {}
    gw_event.pop("multiValueHeaders", None)

    result = app(gw_event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["theme"] == "light"


def test_cookie_param_vpc_lattice_v2(gw_event_vpc_lattice):
    """Test cookie parameter with VPC Lattice v2 (headers are lists)."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = VPCLatticeV2Resolver(enable_validation=True)

    @app.get("/me")
    def handler(session_id: Annotated[str, Cookie()]):
        return {"session_id": session_id}

    gw_event_vpc_lattice["method"] = "GET"
    gw_event_vpc_lattice["path"] = "/me"
    gw_event_vpc_lattice["headers"]["cookie"] = ["session_id=lattice_abc"]

    result = app(gw_event_vpc_lattice, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["session_id"] == "lattice_abc"


def test_cookie_param_vpc_lattice_v1(gw_event_vpc_lattice_v1):
    """Test cookie parameter with VPC Lattice v1 (comma-separated headers)."""
    from aws_lambda_powertools.event_handler.openapi.params import Cookie

    app = VPCLatticeResolver(enable_validation=True)

    @app.get("/me")
    def handler(session_id: Annotated[str, Cookie()]):
        return {"session_id": session_id}

    gw_event_vpc_lattice_v1["method"] = "GET"
    gw_event_vpc_lattice_v1["raw_path"] = "/me"
    gw_event_vpc_lattice_v1["headers"]["cookie"] = "session_id=lattice_v1_abc"

    result = app(gw_event_vpc_lattice_v1, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["session_id"] == "lattice_v1_abc"


def test_alb_response_none_body_with_validation(gw_event_alb):
    # GIVEN an ALBResolver with validation enabled
    app = ALBResolver(enable_validation=True)

    gw_event_alb["path"] = "/no-content"
    gw_event_alb["httpMethod"] = "DELETE"

    # WHEN a handler returns Response with body=None and return type is None
    @app.delete("/no-content")
    def handler() -> None:
        return Response(status_code=204, body=None)

    # THEN the response should be 204 with empty body (not 422 validation error)
    result = app(gw_event_alb, {})
    assert result["statusCode"] == 204
    assert result["body"] == ""


def test_alb_response_typed_none_body_with_validation(gw_event_alb):
    # GIVEN an ALBResolver with validation enabled
    app = ALBResolver(enable_validation=True)

    gw_event_alb["path"] = "/no-content"
    gw_event_alb["httpMethod"] = "DELETE"

    # WHEN a handler returns Response[None] with body=None
    @app.delete("/no-content")
    def handler() -> Response[None]:
        return Response(status_code=204, body=None)

    # THEN the response should be 204 with empty body (not 422 validation error)
    result = app(gw_event_alb, {})
    assert result["statusCode"] == 204
    assert result["body"] == ""
