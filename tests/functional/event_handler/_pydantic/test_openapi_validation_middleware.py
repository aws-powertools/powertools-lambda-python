import base64
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePath
from typing import Dict, List, Optional, Tuple

import pytest
from pydantic import BaseModel, Field
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
from aws_lambda_powertools.event_handler.openapi.params import Body, Form, Header, Query


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


@pytest.mark.skipif(reason="Test temporarily disabled until falsy return is fixed")
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


@pytest.mark.skipif(reason="Test temporarily disabled until falsy return is fixed")
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


@pytest.mark.skipif(reason="Test temporarily disabled until falsy return is fixed")
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

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/form")
    def post_form(name: Annotated[str, Form()], tags: Annotated[List[str], Form()]):
        return {"name": name, "tags": tags}

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/form"
    gw_event["headers"]["content-type"] = "application/x-www-form-urlencoded"
    gw_event["body"] = "name=test&tags=tag1&tags=tag2"

    result = app(gw_event, {})
    assert result["statusCode"] == 200


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


def test_validate_pydantic_query_params_with_config_dict_and_validators(gw_event):
    """Test that Pydantic models with ConfigDict, aliases, and validators work correctly"""
    from typing import Any

    from pydantic import AfterValidator, Base64UrlStr, ConfigDict, StringConstraints, alias_generators

    del gw_event["multiValueHeaders"]
    del gw_event["multiValueQueryStringParameters"]

    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger(path="/swagger")

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
