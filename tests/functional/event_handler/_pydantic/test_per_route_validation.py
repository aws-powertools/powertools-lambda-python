from typing import cast

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from tests.functional.utils import load_event


class TodoItem(BaseModel):
    name: str
    completed: bool = False


def test_per_route_validation_enabled_on_single_route():
    # GIVEN APIGatewayRestResolver with global enable_validation
    # AND one route with explicit enable_validation=True
    # AND one route without explicit validation (inherits global)
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/explicitly-validated", enable_validation=True)
    def explicitly_validated_route() -> TodoItem:
        return TodoItem(name="test", completed=True)

    @app.get("/inherit-validated")
    def inherit_validated_route() -> TodoItem:
        return TodoItem(name="inherit", completed=False)

    # WHEN calling the explicitly validated route
    event = load_event("apiGatewayProxyEvent.json")
    event["path"] = "/explicitly-validated"
    event["httpMethod"] = "GET"

    result = app(event, {})

    # THEN response should be validated and successful
    assert result["statusCode"] == 200
    assert '"name":"test"' in result["body"]

    # WHEN calling the route that inherits validation
    event["path"] = "/inherit-validated"
    result = app(event, {})

    # THEN response should also be validated
    assert result["statusCode"] == 200
    assert "inherit" in result["body"]


def test_per_route_validation_disabled_on_single_route():
    # GIVEN APIGatewayRestResolver with global enable_validation=True
    # AND one route with enable_validation=False
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/validated")
    def validated_route() -> TodoItem:
        return TodoItem(name="test", completed=True)

    @app.get("/not-validated", enable_validation=False)
    def not_validated_route() -> dict:
        # This returns invalid data that doesn't match TodoItem but should not fail
        return {"invalid": "data", "extra": "field"}

    # WHEN calling the validated route
    event = load_event("apiGatewayProxyEvent.json")
    event["path"] = "/validated"
    event["httpMethod"] = "GET"

    result = app(event, {})

    # THEN response should be validated and successful
    assert result["statusCode"] == 200
    assert '"name":"test"' in result["body"]

    # WHEN calling the non-validated route with invalid response
    event["path"] = "/not-validated"
    result = app(event, {})

    # THEN response should bypass validation
    assert result["statusCode"] == 200
    assert "invalid" in result["body"]


def test_per_route_validation_request_body_validation():
    # GIVEN APIGatewayRestResolver WITH global validation enabled
    # AND routes with different validation settings
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/create")
    def create_item(item: TodoItem) -> TodoItem:
        return item

    @app.post("/create-no-validation", enable_validation=False)
    def create_item_no_validation() -> dict:
        # Without validation, we manually parse the body
        body = app.current_event.json_body
        return body

    # WHEN calling validated route with valid body
    event = load_event("apiGatewayProxyEvent.json")
    event["path"] = "/create"
    event["httpMethod"] = "POST"
    event["body"] = '{"name": "New Task", "completed": false}'

    result = app(event, {})

    # THEN request should be validated and successful
    assert result["statusCode"] == 200
    assert "New Task" in result["body"]

    # WHEN calling validated route with invalid body
    event["body"] = '{"invalid": "data"}'
    result = app(event, {})

    # THEN validation should fail with 422
    assert result["statusCode"] == 422

    # WHEN calling non-validated route with any body
    event["path"] = "/create-no-validation"
    event["body"] = '{"invalid": "data"}'
    result = app(event, {})

    # THEN should succeed without validation
    assert result["statusCode"] == 200


def test_per_route_validation_inherits_from_resolver():
    # GIVEN APIGatewayRestResolver with global enable_validation=True
    # AND routes without explicit enable_validation setting
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/route1")
    def route1() -> TodoItem:
        return TodoItem(name="test", completed=True)

    @app.post("/route2")
    def route2(item: TodoItem) -> TodoItem:
        return item

    # WHEN calling routes without explicit validation setting
    event = load_event("apiGatewayProxyEvent.json")
    event["path"] = "/route1"
    event["httpMethod"] = "GET"

    result = app(event, {})

    # THEN they should inherit global validation setting
    assert result["statusCode"] == 200

    # WHEN calling POST with invalid body
    event["path"] = "/route2"
    event["httpMethod"] = "POST"
    event["body"] = '{"invalid": "data"}'

    result = app(event, {})

    # THEN validation should be applied (422 error)
    assert result["statusCode"] == 422


def test_per_route_validation_mixed_routes():
    # GIVEN APIGatewayRestResolver with mixed validation settings
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/always-validated")
    def always_validated() -> TodoItem:
        return TodoItem(name="validated", completed=True)

    @app.get("/never-validated", enable_validation=False)
    def never_validated():
        # Return invalid TodoItem structure
        return {"wrong": "structure"}

    @app.get("/inherit-global")
    def inherit_global() -> TodoItem:
        return TodoItem(name="inherit", completed=False)

    event = load_event("apiGatewayProxyEvent.json")
    event["httpMethod"] = "GET"

    # WHEN calling route with global validation (enable_validation not set)
    event["path"] = "/inherit-global"
    result = app(event, {})
    assert result["statusCode"] == 200
    assert "inherit" in result["body"]

    # WHEN calling route with explicit validation=False returning invalid data
    event["path"] = "/never-validated"
    result = app(event, {})
    # THEN should succeed without validation
    assert result["statusCode"] == 200
    assert "wrong" in result["body"]

    # WHEN calling route with inherited validation
    event["path"] = "/always-validated"
    result = app(event, {})
    assert result["statusCode"] == 200
    assert "validated" in result["body"]


def test_per_route_validation_with_resolver_disabled():
    # GIVEN APIGatewayRestResolver with global validation disabled (default)
    # Note: Per-route enable_validation=True requires the resolver to have
    # enable_validation=True for the middleware to exist. This test documents
    # that you can't opt-in to validation per-route without global validation.
    app = APIGatewayRestResolver()  # enable_validation=False by default

    @app.get("/no-explicit-setting")
    def default_route() -> TodoItem:
        return TodoItem(name="test", completed=True)

    event = load_event("apiGatewayProxyEvent.json")
    event["httpMethod"] = "GET"

    # WHEN calling route without explicit setting (inherits False)
    event["path"] = "/no-explicit-setting"
    result = app(event, {})

    # THEN should not be validated (returns as-is)
    assert result["statusCode"] == 200
    assert "test" in result["body"]


def test_per_route_validation_response_error_code():
    # GIVEN APIGatewayRestResolver with custom response_validation_error_http_code
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/invalid-response")
    def invalid_response() -> TodoItem:
        # Return dict that doesn't match TodoItem model to test validation error handling
        return cast(TodoItem, {"bad": "response"})

    # WHEN calling route that returns invalid response
    event = load_event("apiGatewayProxyEvent.json")
    event["path"] = "/invalid-response"
    event["httpMethod"] = "GET"

    result = app(event, {})

    # THEN should return 422 Unprocessable Entity (default response validation error code)
    assert result["statusCode"] == 422


def test_per_route_validation_with_pydantic_v2():
    """Test that per-route validation actually validates when resolver has validation disabled"""
    # GIVEN APIGatewayRestResolver WITHOUT global validation
    app = APIGatewayRestResolver()

    class Task(BaseModel):
        title: str
        priority: int

    @app.get("/task", enable_validation=True)
    def get_task() -> Task:
        # Return invalid data — missing 'title' and 'priority'
        return cast(Task, {"wrong": "data"})

    @app.get("/unvalidated-task")
    def get_unvalidated_task():
        return {"title": "Anything", "extra": "field"}

    event = load_event("apiGatewayProxyEvent.json")
    event["httpMethod"] = "GET"

    # WHEN calling validated route with invalid data
    event["path"] = "/task"
    result = app(event, {})

    # THEN validation must reject it with 422
    assert result["statusCode"] == 422

    # WHEN calling unvalidated route
    event["path"] = "/unvalidated-task"
    result = app(event, {})

    # THEN should return as-is without validation
    assert result["statusCode"] == 200
    assert "extra" in result["body"]


def test_per_route_opt_in_validation_with_valid_data():
    """Test that per-route opt-in validation passes valid data and serializes correctly"""
    # GIVEN APIGatewayRestResolver WITHOUT global validation
    app = APIGatewayRestResolver()

    class Task(BaseModel):
        title: str
        priority: int

    @app.get("/task", enable_validation=True)
    def get_task() -> Task:
        return Task(title="Important", priority=1)

    event = load_event("apiGatewayProxyEvent.json")
    event["httpMethod"] = "GET"
    event["path"] = "/task"

    # WHEN calling validated route with valid data
    result = app(event, {})

    # THEN validation passes and response is serialized
    assert result["statusCode"] == 200
    assert "Important" in result["body"]
