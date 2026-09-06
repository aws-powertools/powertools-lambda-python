import json
import warnings
from typing import Literal

import pytest
from pydantic import BaseModel, Field, computed_field
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.models import Contact, License, Server
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse


@pytest.mark.usefixtures("pydanticv2_only")
def test_openapi_3_1_simple_handler(openapi31_schema):
    # GIVEN APIGatewayRestResolver is initialized with enable_validation=True
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN we have a simple handler
    @app.get("/")
    def handler():
        pass

    # WHEN we get the schema
    schema = json.loads(app.get_openapi_json_schema())

    # THEN the schema should be valid
    assert openapi31_schema(schema)


@pytest.mark.usefixtures("pydanticv2_only")
def test_openapi_3_0_with_pydantic_v2():
    # GIVEN APIGatewayRestResolver is initialized with enable_validation=True
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN we get the schema
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")
        app.get_openapi_json_schema(openapi_version="3.0.0")
        assert len(w) == 1
        assert str(w[-1].message) == (
            "You are using Pydantic v2, which is incompatible with OpenAPI schema 3.0. Forcing OpenAPI 3.1"
        )


@pytest.mark.usefixtures("pydanticv2_only")
def test_openapi_3_1_complex_handler(openapi31_schema):
    # GIVEN APIGatewayRestResolver is initialized with enable_validation=True
    app = APIGatewayRestResolver(enable_validation=True)

    # GIVEN a complex pydantic model
    class TodoAttributes(BaseModel):
        userId: int
        id_: int | None = Field(alias="id", default=None)
        title: str
        completed: bool

    class Todo(BaseModel):
        type: Literal["ingest"]
        attributes: TodoAttributes

    class TodoEnvelope(BaseModel):
        data: Annotated[Todo, Field(description="The todo")]

    # WHEN we have a complex handler
    @app.get(
        "/",
        summary="This is a summary",
        description="Gets todos",
        tags=["users", "operations", "todos"],
        responses={
            204: OpenAPIResponse(
                description="Successful creation",
                content={"": {"schema": {}}},
            ),
        },
    )
    def handler(
        name: Annotated[str, Query(description="The name", min_length=10, max_length=20)] = "John Doe Junior",
    ) -> TodoEnvelope: ...

    @app.post(
        "/todos",
        tags=["todo"],
        responses={
            204: OpenAPIResponse(
                description="Successful creation",
                content={"": {"schema": {}}},
            ),
        },
    )
    def create_todo(todo: TodoEnvelope): ...

    # WHEN we get the schema
    schema = json.loads(
        app.get_openapi_json_schema(
            title="My little API",
            version="69",
            openapi_version="3.1.0",
            summary="API Summary",
            description="API description",
            tags=["api"],
            servers=[Server(url="http://localhost")],
            terms_of_service="Yes",
            contact=Contact(name="John Smith"),
            license_info=License(name="MIT"),
        ),
    )

    # THEN the schema should be valid
    assert openapi31_schema(schema)


@pytest.mark.usefixtures("pydanticv2_only")
def test_openapi_schema_includes_computed_field():
    # GIVEN a model with a computed_field
    class User(BaseModel):
        first_name: str
        last_name: str

        @computed_field
        @property
        def full_name(self) -> str:
            return f"{self.first_name} {self.last_name}"

    # GIVEN APIGatewayRestResolver with a handler returning that model
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/user")
    def get_user() -> User:
        return User(first_name="John", last_name="Doe")

    # WHEN we get the schema
    schema = json.loads(app.get_openapi_json_schema())

    # THEN the computed_field should appear in the response schema
    user_schema = schema["components"]["schemas"]["User"]
    assert "full_name" in user_schema["properties"]
    assert user_schema["properties"]["full_name"]["type"] == "string"
    assert user_schema["properties"]["full_name"].get("readOnly") is True


@pytest.mark.usefixtures("pydanticv2_only")
def test_openapi_schema_computed_field_not_in_request_body():
    # GIVEN a model with a computed_field used as both request and response
    class Item(BaseModel):
        price: float
        quantity: int

        @computed_field
        @property
        def total(self) -> float:
            return self.price * self.quantity

    # GIVEN APIGatewayRestResolver with handlers using the model
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items")
    def create_item(item: Item) -> Item:
        return item

    # WHEN we get the schema
    schema = json.loads(app.get_openapi_json_schema())

    # THEN the request body schema should NOT include computed_field
    request_body = schema["paths"]["/items"]["post"]["requestBody"]
    request_ref = request_body["content"]["application/json"]["schema"]["$ref"]
    request_schema_name = request_ref.split("/")[-1]

    # THEN the response schema SHOULD include computed_field
    response_ref = schema["paths"]["/items"]["post"]["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    response_schema_name = response_ref.split("/")[-1]

    # When input/output schemas are separate, we expect different schema names
    # When they share a schema, computed_field should be present
    if request_schema_name == response_schema_name:
        # Shared schema - computed_field should be present (serialization mode wins)
        item_schema = schema["components"]["schemas"][response_schema_name]
        assert "total" in item_schema["properties"]
    else:
        # Separate schemas
        input_schema = schema["components"]["schemas"][request_schema_name]
        output_schema = schema["components"]["schemas"][response_schema_name]
        assert "total" not in input_schema["properties"]
        assert "total" in output_schema["properties"]
