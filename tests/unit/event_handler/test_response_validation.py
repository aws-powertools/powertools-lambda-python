import json
from http import HTTPStatus
from typing import Optional

import pytest
from pydantic import BaseModel, Field

from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.openapi.exceptions import ResponseValidationError

app = APIGatewayRestResolver(enable_validation=True)
app_with_custom_response_validation_error = APIGatewayRestResolver(
    enable_validation=True,
    response_validation_error_http_status=HTTPStatus.INTERNAL_SERVER_ERROR,
)


class Todo(BaseModel):
    userId: int
    id_: Optional[int] = Field(alias="id", default=None)
    title: str
    completed: bool


TODO_OBJECT = Todo(userId="1234", id="1", title="Write tests.", completed=True)


@app_with_custom_response_validation_error.get("/string_not_todo")
@app.get("/string_not_todo")
def return_string_not_todo() -> Todo:
    return "hello"


@app_with_custom_response_validation_error.get("/incomplete_todo")
@app.get("/incomplete_todo")
def return_incomplete_todo() -> Todo:
    return {"title": "fix_response_validation"}


@app_with_custom_response_validation_error.get("/todo")
@app.get("/todo")
def return_todo() -> Todo:
    return TODO_OBJECT


# --- Tests below ---


@pytest.fixture()
def event_factory():
    def _factory(path: str):
        return {
            "httpMethod": "GET",
            "path": path,
        }

    yield _factory


@pytest.fixture()
def response_validation_error_factory():
    def _factory(loc: list[str], type_: str):
        if not loc:
            return [{"loc": ["response"], "type": type_}]
        return [{"loc": ["response", location], "type": type_} for location in loc]

    yield _factory


class TestDefaultResponseValidation:

    def test_valid_response(self, event_factory):
        event = event_factory("/todo")

        response = app.resolve(event, None)
        body = json.loads(response["body"])

        assert response["statusCode"] == HTTPStatus.OK
        assert body == TODO_OBJECT.model_dump(by_alias=True)

    @pytest.mark.parametrize(
        (
            "path",
            "error_location",
            "error_type",
        ),
        [
            ("/string_not_todo", [], "model_attributes_type"),
            ("/incomplete_todo", ["userId", "completed"], "missing"),
        ],
        ids=["string_not_todo", "incomplete_todo"],
    )
    def test_default_serialization_failure(
        self,
        path,
        error_location,
        error_type,
        event_factory,
        response_validation_error_factory,
    ):
        """Tests to demonstrate cases when response serialization fails, as expected."""
        event = event_factory(path)
        error_detail = response_validation_error_factory(error_location, error_type)

        response = app.resolve(event, None)
        body = json.loads(response["body"])

        assert response["statusCode"] == HTTPStatus.UNPROCESSABLE_ENTITY
        assert body == {"statusCode": 422, "detail": error_detail}


class TestCustomResponseValidation:

    def test_valid_response(self, event_factory):

        event = event_factory("/todo")

        response = app_with_custom_response_validation_error.resolve(event, None)
        body = json.loads(response["body"])

        assert response["statusCode"] == HTTPStatus.OK
        assert body == TODO_OBJECT.model_dump(by_alias=True)

    @pytest.mark.parametrize(
        (
            "path",
            "error_location",
            "error_type",
        ),
        [
            ("/string_not_todo", [], "model_attributes_type"),
            ("/incomplete_todo", ["userId", "completed"], "missing"),
        ],
        ids=["string_not_todo", "incomplete_todo"],
    )
    def test_custom_serialization_failure(
        self,
        path,
        error_location,
        error_type,
        event_factory,
        response_validation_error_factory,
    ):
        """Tests to demonstrate cases when response serialization fails, as expected."""

        event = event_factory(path)
        error_detail = response_validation_error_factory(error_location, error_type)

        response = app_with_custom_response_validation_error.resolve(event, None)
        body = json.loads(response["body"])

        assert response["statusCode"] == HTTPStatus.INTERNAL_SERVER_ERROR
        assert body == {"statusCode": 500, "detail": error_detail}

    @pytest.mark.parametrize(
        "path",
        [
            ("/string_not_todo"),
            ("/incomplete_todo"),
        ],
        ids=["string_not_todo", "incomplete_todo"],
    )
    def test_sanitized_error_response(
        self,
        path,
        event_factory,
    ):
        event = event_factory(path)

        @app_with_custom_response_validation_error.exception_handler(ResponseValidationError)
        def handle_response_validation_error(ex: ResponseValidationError):
            return Response(
                status_code=500,
                content_type="application/json",
                body="Unexpected response.",
            )

        response = app_with_custom_response_validation_error.resolve(event, None)

        assert response["statusCode"] == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response["body"] == "Unexpected response."
