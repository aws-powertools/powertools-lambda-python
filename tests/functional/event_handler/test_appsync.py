import asyncio
from typing import Optional

import pytest

from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.event_handler.exceptions_appsync import InconsistentPayload, ResolverNotFound
from aws_lambda_powertools.event_handler.graphql_appsync.router import Router
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
        return f"get_locations#{name}"

    @app.resolver(field_name="listLocations2")
    def get_locations2(name: str):
        return f"get_locations2#{name}"

    app.include_router(router)

    # WHEN
    mock_event1 = {"typeName": "Query", "fieldName": "listLocations", "arguments": {"name": "value"}}
    mock_event2 = {"typeName": "Query", "fieldName": "listLocations2", "arguments": {"name": "value"}}
    result1 = app.resolve(mock_event1, LambdaContext())
    result2 = app.resolve(mock_event2, LambdaContext())

    # THEN
    assert result1 == "get_locations#value"
    assert result2 == "get_locations2#value"


def test_resolver_include_mixed_resolver():
    # GIVEN
    app = AppSyncResolver()
    router = Router()

    @router.batch_resolver(type_name="Query", field_name="listLocations")
    def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return f"get_locations#{name}#" + event.source["id"]

    @app.resolver(field_name="listLocations2")
    def get_locations2(name: str) -> str:
        return f"get_locations2#{name}"

    app.include_router(router)

    # WHEN
    mock_event1 = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Query",
            },
            "fieldName": "listLocations",
            "arguments": {"name": "value"},
            "source": {
                "id": "1",
            },
        },
    ]
    mock_event2 = {
        "typeName": "Query",
        "info": {
            "fieldName": "listLocations2",
            "parentTypeName": "Post",
        },
        "fieldName": "listLocations2",
        "arguments": {"name": "value"},
    }

    result1 = app.resolve(mock_event1, LambdaContext())
    result2 = app.resolve(mock_event2, LambdaContext())

    # THEN
    assert result1 == ["get_locations#value#1"]
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
        if router.context.get("is_admin"):
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


# Batch resolver tests
def test_resolve_batch_processing():
    event = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "1",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "2",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": [3, 4],
            },
        },
    ]

    app = AppSyncResolver()

    @app.batch_resolver(field_name="listLocations")
    def create_something(event: AppSyncResolverEvent) -> Optional[list]:  # noqa AA03 VNE003
        return event.source["id"] if event.source else None

    # Call the implicit handler
    result = app.resolve(event, LambdaContext())
    assert result == [appsync_event["source"]["id"] for appsync_event in event]

    assert app.current_batch_event and len(app.current_batch_event) == len(event)
    assert not app.current_event


def test_resolve_batch_processing_with_raise_on_exception():
    event = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "1",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "2",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": [3, 4],
            },
        },
    ]

    app = AppSyncResolver()

    @app.batch_resolver(field_name="listLocations", raise_on_error=True)
    def create_something(event: AppSyncResolverEvent) -> Optional[list]:  # noqa AA03 VNE003
        raise RuntimeError

    # Call the implicit handler
    with pytest.raises(RuntimeError):
        app.resolve(event, LambdaContext())


def test_async_resolve_batch_processing_with_raise_on_exception():
    event = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "1",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "2",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": [3, 4],
            },
        },
    ]

    app = AppSyncResolver()

    @app.async_batch_resolver(field_name="listLocations", raise_on_error=True)
    def create_something(event: AppSyncResolverEvent) -> Optional[list]:  # noqa AA03 VNE003
        raise RuntimeError

    # Call the implicit handler
    with pytest.raises(RuntimeError):
        app.resolve(event, LambdaContext())


def test_resolve_batch_processing_without_exception():
    event = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "1",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "2",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": [3, 4],
            },
        },
    ]

    app = AppSyncResolver()

    @app.batch_resolver(field_name="listLocations", raise_on_error=False)
    def create_something(event: AppSyncResolverEvent) -> Optional[list]:  # noqa AA03 VNE003
        raise RuntimeError

    # Call the implicit handler
    result = app.resolve(event, LambdaContext())
    assert result == [None, None, None]

    assert app.current_batch_event and len(app.current_batch_event) == len(event)
    assert not app.current_event


def test_resolve_async_batch_processing_without_exception():
    event = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "1",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "2",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": [3, 4],
            },
        },
    ]

    app = AppSyncResolver()

    @app.async_batch_resolver(field_name="listLocations", raise_on_error=False)
    def create_something(event: AppSyncResolverEvent) -> Optional[list]:  # noqa AA03 VNE003
        raise RuntimeError

    # Call the implicit handler
    result = app.resolve(event, LambdaContext())
    assert result == [None, None, None]

    assert app.current_batch_event and len(app.current_batch_event) == len(event)
    assert not app.current_event


def test_resolver_batch_resolver_many_fields_with_different_name():
    # GIVEN
    app = AppSyncResolver()
    router = Router()

    @router.batch_resolver(type_name="Query", field_name="listLocations")
    def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return "get_locations#" + name + "#" + event.source["id"]

    app.include_router(router)

    # WHEN
    mock_event1 = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Query",
            },
            "fieldName": "listLocations",
            "arguments": {"name": "value"},
            "source": {
                "id": "1",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocationsDifferent",
                "parentTypeName": "Query",
            },
            "fieldName": "listLocations",
            "arguments": {"name": "value"},
            "source": {
                "id": "1",
            },
        },
    ]

    with pytest.raises(InconsistentPayload):
        app.resolve(mock_event1, LambdaContext())


def test_resolver_batch_with_resolver_not_found():
    # GIVEN a AppSyncResolver
    app = AppSyncResolver()
    router = Router()

    # WHEN we have an event
    # WHEN the event field_name doesn't match with the resolver field_name
    mock_event1 = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listCars",
                "parentTypeName": "Query",
            },
            "fieldName": "listCars",
            "arguments": {"name": "value"},
            "source": {
                "id": "1",
            },
        },
    ]

    @router.batch_resolver(type_name="Query", field_name="listLocations")
    def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return "get_locations#" + name + "#" + event.source["id"]

    app.include_router(router)

    # THEN must fail with ValueError
    with pytest.raises(ResolverNotFound, match="No resolver found for.*"):
        app.resolve(mock_event1, LambdaContext())


def test_resolver_batch_with_sync_and_async_resolver_at_same_time():
    # GIVEN a AppSyncResolver
    app = AppSyncResolver()
    router = Router()

    # WHEN we have an event
    # WHEN the event field_name doesn't match with the resolver field_name
    mock_event1 = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listCars",
                "parentTypeName": "Query",
            },
            "fieldName": "listCars",
            "arguments": {"name": "value"},
            "source": {
                "id": "1",
            },
        },
    ]

    @router.batch_resolver(type_name="Query", field_name="listCars")
    def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return "get_locations#" + name + "#" + event.source["id"]

    @router.async_batch_resolver(type_name="Query", field_name="listCars")
    async def get_locations_async(event: AppSyncResolverEvent, name: str) -> str:
        return "get_locations#" + name + "#" + event.source["id"]

    app.include_router(router)

    # THEN must fail with ValueError
    with pytest.warns(UserWarning, match="Both synchronous and asynchronous resolvers*"):
        app.resolve(mock_event1, LambdaContext())


def test_resolver_include_batch_resolver():
    # GIVEN
    app = AppSyncResolver()
    router = Router()

    @router.batch_resolver(type_name="Query", field_name="listLocations")
    def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return "get_locations#" + name + "#" + event.source["id"]

    @app.batch_resolver(field_name="listLocations2")
    def get_locations2(event: AppSyncResolverEvent, name: str) -> str:
        return "get_locations2#" + name + "#" + event.source["id"]

    app.include_router(router)

    # WHEN
    mock_event1 = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Query",
            },
            "fieldName": "listLocations",
            "arguments": {"name": "value"},
            "source": {
                "id": "1",
            },
        },
    ]
    mock_event2 = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations2",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations2",
            "arguments": {"name": "value"},
            "source": {
                "id": "2",
            },
        },
    ]
    result1 = app.resolve(mock_event1, LambdaContext())
    result2 = app.resolve(mock_event2, LambdaContext())

    # THEN
    assert result1 == ["get_locations#value#1"]
    assert result2 == ["get_locations2#value#2"]


def test_resolve_async_batch_processing():
    event = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "1",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": "2",
            },
        },
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations",
            "arguments": {},
            "source": {
                "id": [3, 4],
            },
        },
    ]

    app = AppSyncResolver()

    @app.async_batch_resolver(field_name="listLocations")
    async def create_something(event: AppSyncResolverEvent) -> Optional[list]:
        return event.source["id"] if event.source else None

    # Call the implicit handler
    result = app.resolve(event, LambdaContext())
    assert result == [appsync_event["source"]["id"] for appsync_event in event]

    assert app.current_batch_event and len(app.current_batch_event) == len(event)


def test_resolve_async_batch_and_sync_singular_processing():
    # GIVEN
    app = AppSyncResolver()
    router = Router()

    @router.async_batch_resolver(type_name="Query", field_name="listLocations")
    async def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return "get_locations#" + name + "#" + event.source["id"]

    @app.resolver(type_name="Query", field_name="listLocation")
    def get_location(name: str) -> str:
        return "get_location#" + name

    app.include_router(router)

    # WHEN
    mock_event1 = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Query",
            },
            "fieldName": "listLocations",
            "arguments": {"name": "value"},
            "source": {
                "id": "1",
            },
        },
    ]
    mock_event2 = {"typeName": "Query", "fieldName": "listLocation", "arguments": {"name": "value"}}

    result1 = app.resolve(mock_event1, LambdaContext())
    result2 = app.resolve(mock_event2, LambdaContext())

    # THEN
    assert result1 == ["get_locations#value#1"]
    assert result2 == "get_location#value"


def test_async_resolver_include_batch_resolver():
    # GIVEN an AppSyncResolver instance and a Router
    app = AppSyncResolver()
    router = Router()

    @router.async_batch_resolver(type_name="Query", field_name="listLocations")
    async def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return "get_locations#" + name + "#" + event.source["id"]

    @app.async_batch_resolver(field_name="listLocations2")
    async def get_locations2(event: AppSyncResolverEvent, name: str) -> str:
        return "get_locations2#" + name + "#" + event.source["id"]

    app.include_router(router)

    # WHEN two different events needs to be resolved
    mock_event1 = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations",
                "parentTypeName": "Query",
            },
            "fieldName": "listLocations",
            "arguments": {"name": "value"},
            "source": {
                "id": "1",
            },
        },
    ]
    mock_event2 = [
        {
            "typeName": "Query",
            "info": {
                "fieldName": "listLocations2",
                "parentTypeName": "Post",
            },
            "fieldName": "listLocations2",
            "arguments": {"name": "value"},
            "source": {
                "id": "2",
            },
        },
    ]

    # WHEN Resolve the events using the AppSyncResolver
    result1 = app.resolve(mock_event1, LambdaContext())
    result2 = app.resolve(mock_event2, LambdaContext())

    # THEN Verify that the results match the expected values
    assert result1 == ["get_locations#value#1"]
    assert result2 == ["get_locations2#value#2"]
