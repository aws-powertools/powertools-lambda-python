from __future__ import annotations

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.models import (
    ParameterInType,
    Schema,
)
from aws_lambda_powertools.event_handler.openapi.params import (
    Body,
    Query,
)

JSON_CONTENT_TYPE = "application/json"


class Todo(BaseModel):
    id: int = Field(examples=[1])
    title: str = Field(examples=["Example 1"])
    priority: float = Field(examples=[0.5])
    completed: bool = Field(examples=[True])


def test_openapi_with_pep563_and_input_model():
    app = APIGatewayRestResolver()

    @app.get("/users", summary="Get Users", operation_id="GetUsers", description="Get paginated users", tags=["Users"])
    def handler(
        count: Annotated[
            int,
            Query(gt=0, lt=100, examples=["Example 1"]),
        ] = 1,
    ):
        print(count)
        raise NotImplementedError()

    schema = app.get_openapi_schema()

    get = schema.paths["/users"].get
    assert len(get.parameters) == 1
    assert get.summary == "Get Users"
    assert get.operationId == "GetUsers"
    assert get.description == "Get paginated users"
    assert get.tags == ["Users"]

    parameter = get.parameters[0]
    assert parameter.required is False
    assert parameter.name == "count"
    assert parameter.in_ == ParameterInType.query
    assert parameter.schema_.type == "integer"
    assert parameter.schema_.default == 1
    assert parameter.schema_.title == "Count"
    assert parameter.schema_.exclusiveMinimum == 0
    assert parameter.schema_.exclusiveMaximum == 100
    assert len(parameter.schema_.examples) == 1
    assert parameter.schema_.examples[0] == "Example 1"


def test_openapi_with_pep563_and_output_model():

    app = APIGatewayRestResolver()

    @app.get("/")
    def handler() -> Todo:
        return Todo(id=0, title="", priority=0.0, completed=False)

    schema = app.get_openapi_schema()
    assert "Todo" in schema.components.schemas
    todo_schema = schema.components.schemas["Todo"]
    assert isinstance(todo_schema, Schema)

    assert "id" in todo_schema.properties
    id_property = todo_schema.properties["id"]
    assert id_property.examples == [1]

    assert "title" in todo_schema.properties
    title_property = todo_schema.properties["title"]
    assert title_property.examples == ["Example 1"]

    assert "priority" in todo_schema.properties
    priority_property = todo_schema.properties["priority"]
    assert priority_property.examples == [0.5]

    assert "completed" in todo_schema.properties
    completed_property = todo_schema.properties["completed"]
    assert completed_property.examples == [True]


def test_openapi_with_pep563_and_annotated_body():

    app = APIGatewayRestResolver()

    @app.post("/todo")
    def create_todo(
        todo_create_request: Annotated[Todo, Body(title="New Todo")],
    ) -> dict:
        return {"message": f"Created todo {todo_create_request.title}"}

    schema = app.get_openapi_schema()
    assert "Todo" in schema.components.schemas
    todo_schema = schema.components.schemas["Todo"]
    assert isinstance(todo_schema, Schema)

    assert "id" in todo_schema.properties
    id_property = todo_schema.properties["id"]
    assert id_property.examples == [1]

    assert "title" in todo_schema.properties
    title_property = todo_schema.properties["title"]
    assert title_property.examples == ["Example 1"]

    assert "priority" in todo_schema.properties
    priority_property = todo_schema.properties["priority"]
    assert priority_property.examples == [0.5]

    assert "completed" in todo_schema.properties
    completed_property = todo_schema.properties["completed"]
    assert completed_property.examples == [True]
