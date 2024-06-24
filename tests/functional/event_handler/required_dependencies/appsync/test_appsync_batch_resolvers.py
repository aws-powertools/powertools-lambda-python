from typing import List, Optional

import pytest

from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.event_handler.graphql_appsync.exceptions import InvalidBatchResponse, ResolverNotFoundError
from aws_lambda_powertools.event_handler.graphql_appsync.router import Router
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.warnings import PowertoolsUserWarning


# TESTS RECEIVING THE EVENT PARTIALLY AND PROCESS EACH RECORD PER TIME.
def test_resolve_batch_processing_with_related_events_one_at_time():
    # GIVEN An event with multiple requests to fetch related posts for different post IDs.
    event = [
        {
            "arguments": {},
            "identity": "None",
            "source": {
                "post_id": "3",
                "title": "Third book",
            },
            "info": {
                "selectionSetList": [
                    "title",
                ],
                "selectionSetGraphQL": "{\n  title\n}",
                "fieldName": "relatedPosts",
                "parentTypeName": "Post",
            },
        },
        {
            "arguments": {},
            "identity": "None",
            "source": {
                "post_id": "4",
                "title": "Fifth book",
            },
            "info": {
                "selectionSetList": [
                    "title",
                ],
                "selectionSetGraphQL": "{\n  title\n}",
                "fieldName": "relatedPosts",
                "parentTypeName": "Post",
            },
        },
        {
            "arguments": {},
            "identity": "None",
            "source": {
                "post_id": "1",
                "title": "First book",
            },
            "info": {
                "selectionSetList": [
                    "title",
                ],
                "selectionSetGraphQL": "{\n  title\n}",
                "fieldName": "relatedPosts",
                "parentTypeName": "Post",
            },
        },
    ]

    # GIVEN A dictionary of posts and a dictionary of related posts.
    posts = {
        "1": {
            "post_id": "1",
            "title": "First book",
        },
        "2": {
            "post_id": "2",
            "title": "Second book",
        },
        "3": {
            "post_id": "3",
            "title": "Third book",
        },
        "4": {
            "post_id": "4",
            "title": "Fourth book",
        },
    }

    posts_related = {
        "1": [posts["2"]],
        "2": [posts["3"], posts["4"], posts["1"]],
        "3": [posts["2"], posts["1"]],
        "4": [posts["3"], posts["1"]],
    }

    app = AppSyncResolver()

    @app.batch_resolver(type_name="Post", field_name="relatedPosts", aggregate=False)
    def related_posts(event: AppSyncResolverEvent) -> Optional[list]:
        return posts_related[event.source["post_id"]]

    # WHEN related_posts function, which is the batch resolver, is called with the event.
    result = app.resolve(event, LambdaContext())

    # THEN the result must be a list of related posts
    assert result == [
        posts_related["3"],
        posts_related["4"],
        posts_related["1"],
    ]


# Batch resolver tests
def test_resolve_batch_processing_with_simple_queries_one_at_time():
    # GIVEN a list of events representing GraphQL queries for listing locations
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

    # WHEN the batch resolver for the listLocations field is defined
    @app.batch_resolver(field_name="listLocations", aggregate=False)
    def create_something(event: AppSyncResolverEvent) -> Optional[list]:  # noqa AA03 VNE003
        return event.source["id"] if event.source else None

    # THEN the resolver should correctly process the batch of queries
    result = app.resolve(event, LambdaContext())
    assert result == [appsync_event["source"]["id"] for appsync_event in event]

    assert app.current_batch_event and len(app.current_batch_event) == len(event)
    assert not app.current_event


def test_resolve_batch_processing_with_raise_on_exception_one_at_time():
    # GIVEN a list of events representing GraphQL queries for listing locations
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

    # WHEN the sync batch resolver for the 'listLocations' field is defined with raise_on_error=True
    @app.batch_resolver(field_name="listLocations", raise_on_error=True, aggregate=False)
    def create_something(event: AppSyncResolverEvent) -> Optional[list]:  # noqa AA03 VNE003
        raise RuntimeError

    # THEN the resolver should raise a RuntimeError when processing the batch of queries
    with pytest.raises(RuntimeError):
        app.resolve(event, LambdaContext())


def test_async_resolve_batch_processing_with_raise_on_exception_one_at_time():
    # GIVEN a list of events representing GraphQL queries for listing locations
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

    # WHEN the async batch resolver for the 'listLocations' field is defined with raise_on_error=True
    @app.async_batch_resolver(field_name="listLocations", raise_on_error=True, aggregate=False)
    async def create_something(event: AppSyncResolverEvent) -> Optional[list]:  # noqa AA03 VNE003
        raise RuntimeError

    # THEN the resolver should raise a RuntimeError when processing the batch of queries
    with pytest.raises(RuntimeError):
        app.resolve(event, LambdaContext())


def test_resolve_batch_processing_without_exception_one_at_time():
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

    @app.batch_resolver(field_name="listLocations", raise_on_error=False, aggregate=False)
    def create_something(event: AppSyncResolverEvent) -> Optional[list]:  # noqa AA03 VNE003
        raise RuntimeError

    # Call the implicit handler
    result = app.resolve(event, LambdaContext())
    assert result == [None, None, None]

    assert app.current_batch_event and len(app.current_batch_event) == len(event)
    assert not app.current_event


def test_resolve_async_batch_processing_without_exception_one_at_time():
    # GIVEN a list of events representing GraphQL queries for listing locations
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

    # WHEN the batch resolver for the 'listLocations' field is defined with raise_on_error=False
    @app.async_batch_resolver(field_name="listLocations", raise_on_error=False, aggregate=False)
    async def create_something(event: AppSyncResolverEvent) -> Optional[list]:  # noqa AA03 VNE003
        raise RuntimeError

    result = app.resolve(event, LambdaContext())

    # THEN the resolver should return None for each event in the batch
    assert len(app.current_batch_event) == len(event)
    assert result == [None, None, None]


def test_resolver_batch_with_resolver_not_found_one_at_time():
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

    @router.batch_resolver(type_name="Query", field_name="listLocations", aggregate=False)
    def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return f"get_locations#{name}#" + event.source["id"]

    app.include_router(router)

    # THEN must fail with ResolverNotFoundError
    with pytest.raises(ResolverNotFoundError, match="No resolver found for.*"):
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

    @router.batch_resolver(type_name="Query", field_name="listCars", aggregate=False)
    def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return f"get_locations#{name}#" + event.source["id"]

    @router.async_batch_resolver(type_name="Query", field_name="listCars", aggregate=False)
    async def get_locations_async(event: AppSyncResolverEvent, name: str) -> str:
        return f"get_locations#{name}#" + event.source["id"]

    app.include_router(router)

    # THEN must raise a PowertoolsUserWarning
    with pytest.warns(PowertoolsUserWarning, match="Both synchronous and asynchronous resolvers*"):
        app.resolve(mock_event1, LambdaContext())


def test_batch_resolver_with_router():
    # GIVEN an AppSyncResolver and a Router instance
    app = AppSyncResolver()
    router = Router()

    @router.batch_resolver(type_name="Query", field_name="listLocations", aggregate=False)
    def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return f"get_locations#{name}#" + event.source["id"]

    @router.batch_resolver(field_name="listLocations2", aggregate=False)
    def get_locations2(event: AppSyncResolverEvent, name: str) -> str:
        return f"get_locations2#{name}#" + event.source["id"]

    # WHEN we include the routes
    app.include_router(router)

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

    # THEN the resolvers should return the expected results
    assert result1 == ["get_locations#value#1"]
    assert result2 == ["get_locations2#value#2"]


def test_resolve_async_batch_processing():
    # GIVEN a list of events representing GraphQL queries for listing locations
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

    # WHEN the async batch resolver for the 'listLocations' field is defined
    @app.async_batch_resolver(field_name="listLocations", aggregate=False)
    async def create_something(event: AppSyncResolverEvent) -> Optional[list]:
        return event.source["id"] if event.source else None

    # THEN the resolver should correctly process the batch of queries asynchronously
    result = app.resolve(event, LambdaContext())
    assert result == [appsync_event["source"]["id"] for appsync_event in event]

    assert app.current_batch_event and len(app.current_batch_event) == len(event)


def test_resolve_async_batch_and_sync_singular_processing():
    # GIVEN a router with an async batch resolver for 'listLocations' and a sync singular resolver for 'listLocation'
    app = AppSyncResolver()
    router = Router()

    @router.async_batch_resolver(type_name="Query", field_name="listLocations", aggregate=False)
    async def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return f"get_locations#{name}#" + event.source["id"]

    @app.resolver(type_name="Query", field_name="listLocation")
    def get_location(name: str) -> str:
        return f"get_location#{name}"

    app.include_router(router)

    # WHEN resolving a batch of events for async 'listLocations' and a singular event for 'listLocation'
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

    # THEN the resolvers should return the expected results
    assert result1 == ["get_locations#value#1"]
    assert result2 == "get_location#value"


def test_async_resolver_include_batch_resolver():
    # GIVEN an AppSyncResolver instance and a Router
    app = AppSyncResolver()
    router = Router()

    @router.async_batch_resolver(type_name="Query", field_name="listLocations", aggregate=False)
    async def get_locations(event: AppSyncResolverEvent, name: str) -> str:
        return f"get_locations#{name}#" + event.source["id"]

    @app.async_batch_resolver(field_name="listLocations2", aggregate=False)
    async def get_locations2(event: AppSyncResolverEvent, name: str) -> str:
        return f"get_locations2#{name}#" + event.source["id"]

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


def test_resolve_batch_processing_with_simple_queries_with_aggregate():
    # GIVEN a list of events representing GraphQL queries for listing locations
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

    # WHEN the batch resolver for the listLocations field is defined
    @app.batch_resolver(field_name="listLocations")
    def create_something(event: List[AppSyncResolverEvent]) -> Optional[list]:  # noqa AA03 VNE003
        results = []
        for record in event:
            results.append(record.source.get("id") if record.source else None)

        return results

    # THEN the resolver should correctly process the batch of queries
    result = app.resolve(event, LambdaContext())
    assert result == [appsync_event["source"]["id"] for appsync_event in event]

    assert app.current_batch_event and len(app.current_batch_event) == len(event)
    assert not app.current_event


def test_resolve_async_batch_processing_with_simple_queries_with_aggregate():
    # GIVEN a list of events representing GraphQL queries for listing locations
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

    # WHEN the batch resolver for the listLocations field is defined
    @app.async_batch_resolver(field_name="listLocations")
    async def create_something(event: List[AppSyncResolverEvent]) -> Optional[list]:  # noqa AA03 VNE003
        results = []
        for record in event:
            results.append(record.source.get("id") if record.source else None)

        return results

    # THEN the resolver should correctly process the batch of queries
    result = app.resolve(event, LambdaContext())
    assert result == [appsync_event["source"]["id"] for appsync_event in event]

    assert app.current_batch_event and len(app.current_batch_event) == len(event)
    assert not app.current_event


def test_resolve_batch_processing_with_aggregate_and_returning_a_non_list():
    # GIVEN a list of events representing GraphQL queries for listing locations
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
    ]

    app = AppSyncResolver()

    # WHEN the batch resolver for the listLocations field is defined
    @app.batch_resolver(field_name="listLocations")
    def create_something(event: List[AppSyncResolverEvent]) -> Optional[list]:  # noqa AA03 VNE003
        return event[0].source.get("id") if event[0].source else None

    # THEN the resolver should raise a RuntimeError when processing the batch of queries
    with pytest.raises(InvalidBatchResponse):
        app.resolve(event, LambdaContext())


def test_resolve_async_batch_processing_with_aggregate_and_returning_a_non_list():
    # GIVEN a list of events representing GraphQL queries for listing locations
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
    ]

    app = AppSyncResolver()

    # WHEN the batch resolver for the listLocations field is defined
    @app.async_batch_resolver(field_name="listLocations")
    async def create_something(event: List[AppSyncResolverEvent]) -> Optional[list]:  # noqa AA03 VNE003
        return event[0].source.get("id") if event[0].source else None

    # THEN the resolver should raise a RuntimeError when processing the batch of queries
    with pytest.raises(InvalidBatchResponse):
        app.resolve(event, LambdaContext())
