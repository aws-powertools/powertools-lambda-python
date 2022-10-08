import asyncio
import sys

import pytest

from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.event_handler.appsync import Router
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.utils import load_event


def test_direct_resolver():
    # Check whether we can handle an example appsync direct resolver
    mock_event = load_event("appSyncDirectResolver.json")

    app = AppSyncResolver()

    @app.resolver(field_name="createSomething")
    def create_something(id: str):  # noqa AA03 VNE003
        assert app.lambda_context == {}
        return id

    # Call the implicit handler
    result = app(mock_event, {})

    assert result == "my identifier"


def test_amplify_resolver():
    # Check whether we can handle an example appsync resolver
    mock_event = load_event("appSyncResolverEvent.json")

    app = AppSyncResolver()

    @app.resolver(type_name="Merchant", field_name="locations")
    def get_location(page: int, size: int, name: str):
        assert app.current_event is not None
        assert isinstance(app.current_event, AppSyncResolverEvent)
        assert page == 2
        assert size == 1
        return name

    def handler(event, context):
        # Call the explicit resolve function
        return app.resolve(event, context)

    result = handler(mock_event, {})
    assert result == "value"


def test_resolver_no_params():
    # GIVEN
    app = AppSyncResolver()

    @app.resolver(type_name="Query", field_name="noParams")
    def no_params():
        return "no_params has no params"

    event = {"typeName": "Query", "fieldName": "noParams", "arguments": {}}

    # WHEN
    result = app.resolve(event, LambdaContext())

    # THEN
    assert result == "no_params has no params"


def test_resolver_value_error():
    # GIVEN no defined field resolver
    app = AppSyncResolver()

    # WHEN
    with pytest.raises(ValueError) as exp:
        event = {"typeName": "type", "fieldName": "field", "arguments": {}}
        app.resolve(event, LambdaContext())

    # THEN
    assert exp.value.args[0] == "No resolver found for 'type.field'"


def test_resolver_yield():
    # GIVEN
    app = AppSyncResolver()

    mock_event = {"typeName": "Customer", "fieldName": "field", "arguments": {}}

    @app.resolver(field_name="field")
    def func_yield():
        yield "value"

    # WHEN
    mock_context = LambdaContext()
    result = app.resolve(mock_event, mock_context)

    # THEN
    assert next(result) == "value"


def test_resolver_multiple_mappings():
    # GIVEN
    app = AppSyncResolver()

    @app.resolver(field_name="listLocations")
    @app.resolver(field_name="locations")
    def get_locations(name: str, description: str = ""):
        return name + description

    # WHEN
    mock_event1 = {"typeName": "Query", "fieldName": "listLocations", "arguments": {"name": "value"}}
    mock_event2 = {
        "typeName": "Merchant",
        "fieldName": "locations",
        "arguments": {"name": "value2", "description": "description"},
    }
    result1 = app.resolve(mock_event1, LambdaContext())
    result2 = app.resolve(mock_event2, LambdaContext())

    # THEN
    assert result1 == "value"
    assert result2 == "value2description"


@pytest.mark.skipif(sys.version_info < (3, 8), reason="only for python versions that support asyncio.run")
def test_resolver_async():
    # GIVEN
    app = AppSyncResolver()

    mock_event = {"typeName": "Customer", "fieldName": "field", "arguments": {}}

    @app.resolver(field_name="field")
    async def get_async():
        await asyncio.sleep(0.0001)
        return "value"

    # WHEN
    mock_context = LambdaContext()
    result = app.resolve(mock_event, mock_context)

    # THEN
    assert asyncio.run(result) == "value"


def test_resolve_custom_data_model():
    # Check whether we can handle an example appsync direct resolver
    mock_event = load_event("appSyncDirectResolver.json")

    class MyCustomModel(AppSyncResolverEvent):
        @property
        def country_viewer(self):
            return self.request_headers.get("cloudfront-viewer-country")

    app = AppSyncResolver()

    @app.resolver(field_name="createSomething")
    def create_something(id: str):  # noqa AA03 VNE003
        return id

    # Call the implicit handler
    result = app(event=mock_event, context=LambdaContext(), data_model=MyCustomModel)

    assert result == "my identifier"

    assert app.current_event.country_viewer == "US"


def test_resolver_include_resolver():
    # GIVEN
    app = AppSyncResolver()
    router = Router()

    @router.resolver(type_name="Query", field_name="listLocations")
    def get_locations(name: str):
        return "get_locations#" + name

    @app.resolver(field_name="listLocations2")
    def get_locations2(name: str):
        return "get_locations2#" + name

    app.include_router(router)

    # WHEN
    mock_event1 = {"typeName": "Query", "fieldName": "listLocations", "arguments": {"name": "value"}}
    mock_event2 = {"typeName": "Query", "fieldName": "listLocations2", "arguments": {"name": "value"}}
    result1 = app.resolve(mock_event1, LambdaContext())
    result2 = app.resolve(mock_event2, LambdaContext())

    # THEN
    assert result1 == "get_locations#value"
    assert result2 == "get_locations2#value"


def test_append_context():
    app = AppSyncResolver()
    app.append_context(is_admin=True)
    assert app.context.get("is_admin") is True


def test_router_append_context():
    router = Router()
    router.append_context(is_admin=True)
    assert router.context.get("is_admin") is True


def test_route_context_is_cleared_after_resolve():
    # GIVEN
    app = AppSyncResolver()
    event = {"typeName": "Query", "fieldName": "listLocations", "arguments": {"name": "value"}}

    @app.resolver(field_name="listLocations")
    def get_locations(name: str):
        return f"get_locations#{name}"

    # WHEN event resolution kicks in
    app.append_context(is_admin=True)
    app.resolve(event, {})

    # THEN context should be empty
    assert app.context == {}


def test_router_has_access_to_app_context():
    # GIVEN
    app = AppSyncResolver()
    router = Router()
    event = {"typeName": "Query", "fieldName": "listLocations", "arguments": {"name": "value"}}

    @router.resolver(type_name="Query", field_name="listLocations")
    def get_locations(name: str):
        if router.context["is_admin"]:
            return f"get_locations#{name}"

    app.include_router(router)

    # WHEN
    app.append_context(is_admin=True)
    ret = app.resolve(event, {})

    # THEN
    assert ret == "get_locations#value"
    assert router.context == {}


def test_include_router_merges_context():
    # GIVEN
    app = AppSyncResolver()
    router = Router()

    # WHEN
    app.append_context(is_admin=True)
    router.append_context(product_access=True)

    app.include_router(router)

    assert app.context == router.context
