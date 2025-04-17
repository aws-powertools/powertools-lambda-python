import asyncio
from copy import deepcopy

import pytest

from aws_lambda_powertools.event_handler import AppSyncEventsResolver
from aws_lambda_powertools.event_handler.events_appsync.exceptions import UnauthorizedException
from aws_lambda_powertools.event_handler.events_appsync.router import Router
from aws_lambda_powertools.warnings import PowertoolsUserWarning
from tests.functional.utils import load_event


class LambdaContext:
    def __init__(self):
        self.function_name = "test-func"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:eu-west-1:809313241234:function:test-func"
        self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    def get_remaining_time_in_millis(self) -> int:
        return 1000


@pytest.fixture(scope="module")
def lambda_context() -> LambdaContext:
    """Create a new LambdaContext instance for each test module."""
    return LambdaContext()


@pytest.fixture(scope="module")
def mock_event():
    """Load a sample AppSyncEventsEvent for each test module."""
    return load_event("appSyncEventsEvent.json")


def test_publish_event_with_synchronous_resolver(lambda_context, mock_event):
    """Test handling a publish event with a synchronous resolver."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]
    lambda_context = LambdaContext()

    # GIVEN an AppSyncEventsResolver with a synchronous resolver
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def test_handler(payload):
        return {"processed": True, "data": payload["data"]}

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get the correct response
    expected_result = {
        "events": [
            {"id": "123", "payload": {"processed": True, "data": "test data"}},
        ],
    }
    assert result == expected_result


def test_publish_event_with_async_resolver(lambda_context, mock_event):
    """Test handling a publish event with an asynchronous resolver."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with an asynchronous resolver
    app = AppSyncEventsResolver()

    @app.async_on_publish(path="/default/*")
    async def test_handler(payload):
        await asyncio.sleep(0.01)  # Simulate async work
        return {"processed": True, "data": payload["data"]}

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get the correct response
    assert "events" in result
    assert len(result["events"]) == 1
    assert result["events"][0]["payload"]["processed"] is True
    assert result["events"][0]["payload"]["data"] == "test data"


def test_publish_event_with_error_handling(lambda_context, mock_event):
    """Test error handling during publish event processing."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with a resolver that raises an exception
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def test_handler(payload):
        raise ValueError("Test error")

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get an error response
    assert "events" in result
    assert "error" in result["events"][0]
    assert "ValueError - Test error" in result["events"][0]["error"]
    assert result["events"][0]["id"] == "123"


def test_publish_event_with_router_inclusion(lambda_context, mock_event):
    """Test including a router in the AppSyncEventsResolver."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data", "from_router": True}},
    ]

    # GIVEN a router with a resolver
    router = Router()

    @router.on_publish(path="/chat/*")
    def router_handler(payload):
        return {"from_router": True, "data": payload["data"]}

    # GIVEN an AppSyncEventsResolver that includes the router
    app = AppSyncEventsResolver()
    app.include_router(router)

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get the response from the router's handler
    expected_result = {
        "events": [
            {"id": "123", "payload": {"from_router": True, "data": "test data"}},
        ],
    }
    assert result == expected_result


def test_publish_event_with_custom_context(lambda_context, mock_event):
    """Test resolving events with custom context data."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with custom context
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def test_handler(payload):
        # Access the context within the handler
        return {
            "processed": True,
            "data": payload["data"],
            "user_id": app.context.get("user_id"),
            "role": app.context.get("role"),
        }

    # WHEN we resolve the event
    app.append_context(user_id="test-user", role="admin")
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get the response with context data
    expected_result = {
        "events": [
            {
                "id": "123",
                "payload": {
                    "processed": True,
                    "data": "test data",
                    "user_id": "test-user",
                    "role": "admin",
                },
            },
        ],
    }
    assert result == expected_result


def test_publish_event_with_aggregate_mode(lambda_context, mock_event):
    """Test handling a publish event with aggregate mode enabled."""
    # GIVEN a sample publish event with multiple items
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data 1"}},
        {"id": "456", "payload": {"data": "test data 2"}},
    ]

    # GIVEN an AppSyncEventsResolver with an aggregate resolver
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*", aggregate=True)
    def test_batch_handler(payload):
        # Process all events at once
        return [{"batch_processed": True, "data": item["payload"]["data"]} for item in payload]

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get the batch processed response
    expected_result = {
        "events": [
            {"batch_processed": True, "data": "test data 1"},
            {"batch_processed": True, "data": "test data 2"},
        ],
    }
    assert result == expected_result


def test_async_publish_event_with_aggregate_mode(lambda_context, mock_event):
    """Test handling an async publish event with aggregate mode enabled."""
    # GIVEN a sample publish event with multiple items
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data 1"}},
        {"id": "456", "payload": {"data": "test data 2"}},
    ]

    # GIVEN an AppSyncEventsResolver with an async aggregate resolver
    app = AppSyncEventsResolver()

    @app.async_on_publish(path="/default/*", aggregate=True)
    async def test_async_batch_handler(payload):
        # Simulate async processing of all events
        await asyncio.sleep(0.01)
        return [{"async_batch_processed": True, "data": item["payload"]["data"]} for item in payload]

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get the batch processed response
    expected_result = {
        "events": [
            {"async_batch_processed": True, "data": "test data 1"},
            {"async_batch_processed": True, "data": "test data 2"},
        ],
    }
    assert result == expected_result


def test_publish_event_no_matching_resolver(lambda_context, mock_event):
    """Test handling a publish event when no matching resolver is found."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/unknown/path"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with no matching resolver
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def test_handler(payload):
        return {"processed": True}

    # WHEN we resolve the event with a warning
    with pytest.warns(PowertoolsUserWarning, match="No resolvers were found for publish operations"):
        result = app.resolve(mock_event, lambda_context)

    # THEN we should get the original payload returned as is
    expected_result = {
        "events": [
            {"id": "123", "payload": {"data": "test data"}},
        ],
    }
    assert result == expected_result


def test_multiple_resolvers_for_same_path(lambda_context, mock_event):
    """Test behavior when both sync and async resolvers exist for the same path."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/default/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"sync_processed": True, "data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with both sync and async resolvers for the same path
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def sync_handler(payload):
        return {"sync_processed": True, "data": payload["data"]}

    @app.async_on_publish(path="/default/*")
    async def async_handler(event):
        await asyncio.sleep(0.01)
        return {"async_processed": True, "data": event["data"]}

    # WHEN we resolve the event, with a warning expected
    with pytest.warns(PowertoolsUserWarning, match="Both synchronous and asynchronous resolvers found"):
        result = app.resolve(mock_event, lambda_context)

    # THEN the sync resolver should be used (takes precedence)
    expected_result = {
        "events": [
            {"id": "123", "payload": {"sync_processed": True, "data": "test data"}},
        ],
    }
    assert result == expected_result


def test_custom_exception_handling(lambda_context, mock_event):
    """Test handling custom exceptions during event processing."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"sync_processed": True, "data": "test data"}},
    ]

    # GIVEN a custom exception class
    class NotAuthorized(Exception):
        pass

    # GIVEN an AppSyncEventsResolver with a resolver that raises a custom exception
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def test_handler(payload):
        if payload["data"] == "test data":
            raise NotAuthorized("Not authorized")
        return {"processed": True}

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get an error response with our custom exception
    assert "events" in result
    assert "error" in result["events"][0]
    assert "NotAuthorized - Not authorized" in result["events"][0]["error"]
    assert result["events"][0]["id"] == "123"


def test_async_resolver_with_error_handling(lambda_context, mock_event):
    """Test error handling with async resolvers during publish event processing."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"sync_processed": True, "data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with an async resolver that raises an exception
    app = AppSyncEventsResolver()

    @app.async_on_publish(path="/default/*")
    async def test_handler(payload):
        await asyncio.sleep(0.01)  # Simulate async work
        raise ValueError("Async test error")

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get an error response
    assert "events" in result
    assert len(result["events"]) == 1
    assert "error" in result["events"][0]
    assert "ValueError - Async test error" in result["events"][0]["error"]


def test_lambda_handler_with_call_method(lambda_context, mock_event):
    """Test that the lambda handler function properly processes events."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"sync_processed": True, "data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver setup
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def test_handler(payload):
        return {"lambda_processed": True, "data": payload["data"]}

    # WHEN we use the AppSyncEventsResolver as a Lambda handler
    result = app(mock_event, lambda_context)  # Using __call__ method which calls resolve()

    # THEN we should get the processed response
    expected_result = {
        "events": [
            {"id": "123", "payload": {"lambda_processed": True, "data": "test data"}},
        ],
    }
    assert result == expected_result


def test_event_with_mixed_success_and_errors(lambda_context, mock_event):
    """Test handling a batch of events with mixed success and failure outcomes."""
    # GIVEN a sample publish event with multiple items
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "good data"}},
        {"id": "456", "payload": {"data": "bad data"}},
        {"id": "789", "payload": {"data": "good data again"}},
    ]

    # GIVEN an AppSyncEventsResolver with a resolver that conditionally fails
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def test_handler(payload):
        if payload["data"] == "bad data":
            raise ValueError("Bad data detected")
        return {"success": True, "data": payload["data"]}

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get mixed results with success and error responses
    assert "events" in result
    assert len(result["events"]) == 3

    # First event should be successful
    assert "payload" in result["events"][0]
    assert result["events"][0]["payload"]["success"] is True
    assert result["events"][0]["payload"]["data"] == "good data"

    # Second event should have an error
    assert "error" in result["events"][1]
    assert "ValueError - Bad data detected" in result["events"][1]["error"]

    # Third event should be successful
    assert "payload" in result["events"][2]
    assert result["events"][2]["payload"]["success"] is True
    assert result["events"][2]["payload"]["data"] == "good data again"


def test_router_with_context_sharing(lambda_context, mock_event):
    """Test that context is properly shared between routers and the main resolver."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/chat/message"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN a router with context
    router = Router()
    router.append_context(service="chat")

    @router.on_publish(path="/chat/*")
    def router_handler(payload):
        # Access shared context
        return {
            "from_router": True,
            "service": router.context.get("service"),
            "tenant": router.context.get("tenant"),
        }

    # GIVEN an AppSyncEventsResolver with its own context
    app = AppSyncEventsResolver()
    app.append_context(tenant="acme")

    # Include the router and merge contexts
    app.include_router(router)

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the handler should have access to merged context from both sources
    expected_result = {
        "events": [
            {
                "id": "123",
                "payload": {
                    "from_router": True,
                    "service": "chat",
                    "tenant": "acme",
                },
            },
        ],
    }
    assert result == expected_result


def test_context_cleared_after_resolution(lambda_context, mock_event):
    """Test that context is properly cleared after event resolution."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"sync_processed": True, "data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with context data
    app = AppSyncEventsResolver()
    app.append_context(request_id="12345")

    @app.on_publish(path="/default/*")
    def test_handler(payload):
        # Verify context exists during handler execution
        assert app.context.get("request_id") == "12345"
        return {"processed": True}

    # WHEN we resolve the event
    app.resolve(mock_event, lambda_context)

    # THEN the context should be cleared afterward
    assert app.context == {}


def test_path_matching_mechanism(mocker, lambda_context, mock_event):
    """Test the path matching mechanism for resolvers."""

    mock_find_resolver = mocker.patch(
        "aws_lambda_powertools.event_handler.events_appsync._registry.ResolverEventsRegistry.find_resolver",
    )
    # GIVEN a resolver that should be found
    mock_resolver = {
        "func": lambda payload: {"matched": True},
        "aggregate": False,
    }
    mock_find_resolver.return_value = mock_resolver

    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/chat/room/123/message"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver
    app = AppSyncEventsResolver()

    # WHEN we resolve the event
    app.resolve(mock_event, lambda_context)

    # THEN the registry should be queried with the correct path
    mock_find_resolver.assert_called_with("/chat/room/123/message")


def test_async_aggregate_with_parallel_processing(lambda_context, mock_event):
    """Test that async aggregate handlers can process events in parallel."""
    # GIVEN a sample publish event with multiple items
    mock_event["info"]["channel"]["path"] = "/default/process"
    mock_event["events"] = [
        {"id": "123", "payload": {"sync_processed": True, "data": "item 1", "delay": 0.03}},
        {"id": "456", "payload": {"sync_processed": True, "data": "item 2", "delay": 0.02}},
        {"id": "789", "payload": {"sync_processed": True, "data": "item 3", "delay": 0.01}},
    ]

    # GIVEN an AppSyncEventsResolver with an async aggregate handler
    app = AppSyncEventsResolver()

    @app.async_on_publish(path="/default/*", aggregate=True)
    async def test_async_handler(payload):
        # Create tasks for each event with different delays
        tasks = []
        for idx_event in payload:
            tasks.append(process_single_event(idx_event["payload"]))

        # Process all events in parallel
        results = await asyncio.gather(*tasks)
        return results

    async def process_single_event(payload):
        # Simulate variable processing time
        await asyncio.sleep(payload["delay"])
        return {"processed": True, "data": payload["data"]}

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN all events should be processed
    assert "events" in result
    assert len(result["events"]) == 3

    # Check all items were processed
    processed_data = [item["data"] for item in result["events"]]
    assert "item 1" in processed_data
    assert "item 2" in processed_data
    assert "item 3" in processed_data


def test_both_app_and_router_for_same_path(lambda_context, mock_event):
    """Test precedence when both app and router have resolvers for the same path."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/default/duplicate"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN a router with a resolver
    router = Router()

    @router.on_publish(path="/default/duplicate")
    def router_handler(payload):
        return {"source": "router"}

    # GIVEN an AppSyncEventsResolver with a resolver for the same path
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/duplicate")
    def app_handler(payload):
        return {"source": "app"}

    # Include the router after defining the app handler
    app.include_router(router)

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the router's handler should take precedence as it was registered last
    expected_result = {
        "events": [
            {"id": "123", "payload": {"source": "router"}},
        ],
    }
    assert result == expected_result


def test_event_with_real_world_example(lambda_context, mock_event):
    """Test handling a more complex, real-world-like example."""
    # GIVEN a more realistic publish event with multiple items
    mock_event["info"]["channel"]["path"] = "/chat/messages"
    mock_event["events"] = [
        {
            "id": "message-123",
            "payload": {
                "type": "text",
                "content": "Hello, world!",
                "timestamp": 1636718400000,
                "sender": "user1",
            },
        },
        {
            "id": "message-456",
            "payload": {
                "type": "image",
                "content": "https://example.com/image.jpg",
                "timestamp": 1636718500000,
                "sender": "user2",
            },
        },
    ]

    # GIVEN a router for chat-related operations
    chat_router = Router()

    @chat_router.on_publish(path="/chat/*")
    def process_message(payload):
        # Process message based on type
        if payload["type"] == "text":
            return {
                "processed": True,
                "messageType": "text",
                "displayContent": payload["content"],
                "timestamp": payload["timestamp"],
                "sender": payload["sender"],
            }
        elif payload["type"] == "image":
            return {
                "processed": True,
                "messageType": "image",
                "displayContent": f"[Image] {payload['content']}",
                "timestamp": payload["timestamp"],
                "sender": payload["sender"],
            }
        else:
            return {
                "processed": False,
                "error": "Unsupported message type",
            }

    # GIVEN an AppSyncEventsResolver that includes the router
    app = AppSyncEventsResolver()
    app.include_router(chat_router)

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get properly processed messages
    assert "events" in result
    assert len(result["events"]) == 2

    # Check text message
    assert result["events"][0]["id"] == "message-123"
    assert result["events"][0]["payload"]["processed"] is True
    assert result["events"][0]["payload"]["messageType"] == "text"
    assert result["events"][0]["payload"]["displayContent"] == "Hello, world!"

    # Check image message
    assert result["events"][1]["id"] == "message-456"
    assert result["events"][1]["payload"]["processed"] is True
    assert result["events"][1]["payload"]["messageType"] == "image"
    assert result["events"][1]["payload"]["displayContent"] == "[Image] https://example.com/image.jpg"


def test_event_response_with_custom_error_handling(lambda_context, mock_event):
    """Test handling events with custom error handling logic."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/default/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "sensitive data"}},
    ]

    # GIVEN a custom exception and a router with an async handler
    class CustomSecurityException(Exception):
        pass

    router = Router()

    @router.async_on_publish(path="/default/*")
    async def security_check(payload):
        # Simulate a security check that blocks certain IDs
        blocked_data = ["sensitive data"]
        if payload["data"] in blocked_data:
            raise CustomSecurityException("Security check failed: Blocked ID")

        await asyncio.sleep(0.01)  # Simulate async work
        return {"security_verified": True, "data": payload["data"]}

    # GIVEN an AppSyncEventsResolver
    app = AppSyncEventsResolver()
    app.include_router(router)

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get a security error response
    assert "events" in result
    assert len(result["events"]) == 1
    assert "error" in result["events"][0]
    assert "CustomSecurityException - Security check failed" in result["events"][0]["error"]
    assert result["events"][0]["id"] == "123"


def test_pattern_matching_no_valid_paths(lambda_context, mock_event):
    """Test that path pattern matching works correctly with wildcards."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/users/123/notifications/new"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "user notification data"}},
    ]

    # GIVEN an AppSyncEventsResolver with wildcard path patterns
    app = AppSyncEventsResolver()

    # Define multiple resolvers with different path patterns
    @app.on_publish(path="/users/*/notifications/*")  # Should not match
    def user_notification_handler(payload):
        return {"handler": "wildcard_match", "data": "modified data 1"}

    @app.on_publish(path="/users/123/messages/*")  # Should not match
    def user_message_handler(payload):
        return {"handler": "wrong_path", "data": "modified data 2"}

    @app.on_publish(path="/*/*/*")  # should not match
    def generic_handler(payload):
        return {"handler": "generic", "data": "modified data 3"}

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN no resolver is found and we return as is
    expected_result = {
        "events": [
            {"id": "123", "payload": {"data": "user notification data"}},
        ],
    }
    assert result == expected_result


def test_nested_async_functions(lambda_context, mock_event):
    """Test that nested async functions work correctly within resolvers."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/default/nested"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with a resolver that uses nested async functions
    app = AppSyncEventsResolver()

    @app.async_on_publish(path="/default/*")
    async def outer_handler(payload):
        # Define nested async functions
        async def validate_data(data):
            await asyncio.sleep(0.01)  # Simulate validation
            return data.strip() != ""

        async def transform_data(data):
            await asyncio.sleep(0.01)  # Simulate transformation
            return data.upper()

        # Use nested async functions
        is_valid = await validate_data(payload["data"])
        if not is_valid:
            return {"error": "Invalid data"}

        transformed = await transform_data(payload["data"])
        return {"validated": is_valid, "transformed": transformed}

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the nested async functions should execute correctly
    assert "events" in result
    assert len(result["events"]) == 1
    assert result["events"][0]["payload"]["validated"] is True
    assert result["events"][0]["payload"]["transformed"] == "TEST DATA"


def test_concurrent_event_processing(lambda_context, mock_event):
    """Test that multiple events are processed concurrently with async handlers."""
    # GIVEN a sample publish event with multiple items that take different times to process
    mock_event["info"]["channel"]["path"] = "/default/concurrent"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "fast data", "delay": 0.01}},
        {"id": "456", "payload": {"data": "slow data", "delay": 0.03}},
        {"id": "789", "payload": {"data": "medium data", "delay": 0.02}},
    ]

    # GIVEN an AppSyncEventsResolver with an async handler
    app = AppSyncEventsResolver()

    @app.async_on_publish(path="/default/*")
    async def process_with_variable_delay(payload):
        # Simulate processing with different delays
        await asyncio.sleep(payload["delay"])
        return {
            "processed": True,
            "data": payload["data"],
            "processing_time": payload["delay"],
        }

    # WHEN we resolve the event
    import time

    start_time = time.time()
    result = app.resolve(mock_event, lambda_context)
    end_time = time.time()

    # THEN all events should be processed
    assert "events" in result
    assert len(result["events"]) == 3

    # The total time should be roughly equal to the longest individual delay
    # (not the sum of all delays, which would indicate sequential processing)
    processing_time = end_time - start_time
    assert processing_time < 0.1  # Should be close to the max delay (0.03) plus overhead

    # Check all events were processed
    ids = [event.get("id") for event in result["events"]]
    assert set(ids) == {"123", "456", "789"}


def test_handler_with_implicit_call_method_in_lambda_function(lambda_context, mock_event):
    """Test that the __call__ method works correctly as an implicit Lambda handler."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def test_handler(payload):
        return {"processed": True, "data": payload["data"]}

    # Define a Lambda handler using the app directly
    def lambda_handler(event, context):
        return app(event, context)  # Using __call__ method

    # WHEN we call the lambda handler
    result = lambda_handler(mock_event, lambda_context)

    # THEN we should get the expected result
    expected_result = {
        "events": [
            {"id": "123", "payload": {"processed": True, "data": "test data"}},
        ],
    }
    assert result == expected_result


def test_middleware_like_functionality(lambda_context, mock_event):
    """Test implementing middleware-like functionality with context."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver
    app = AppSyncEventsResolver()

    # Simulate middleware by adding context before processing
    def add_request_metadata(event, context, app):
        app.append_context(
            request_id="req-123",
            timestamp=123456789,
            user_agent="test-agent",
        )

    # Handler that uses the context added by middleware
    @app.on_publish(path="/default/*")
    def handler_with_middleware_data(payload):
        return {
            "processed": True,
            "data": payload["data"],
            "metadata": {
                "request_id": app.context.get("request_id"),
                "timestamp": app.context.get("timestamp"),
                "user_agent": app.context.get("user_agent"),
            },
        }

    # WHEN we add middleware data and resolve the event
    add_request_metadata(mock_event, lambda_context, app)
    result = app.resolve(mock_event, lambda_context)

    # THEN the handler should have access to middleware-added context
    expected_metadata = {
        "request_id": "req-123",
        "timestamp": 123456789,
        "user_agent": "test-agent",
    }

    assert result["events"][0]["payload"]["metadata"] == expected_metadata


def test_handler_with_event_transformation(lambda_context, mock_event):
    """Test handlers that transform event data before processing."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/default/transform"
    mock_event["events"] = [
        {"id": "123", "payload": {"user_data": {"name": "John", "age": 30}}},
        {"id": "456", "payload": {"user_data": {"name": "Jane", "age": 16}}},
    ]

    # GIVEN an AppSyncEventsResolver with a router
    router = Router()

    # Add middleware context to transform data
    @router.on_publish(path="/default/*", aggregate=True)
    def transform_and_process(payload):
        # Transform the payload structure
        transformed = []
        for item in payload:
            transformed.append(
                {
                    "id": item["id"],
                    "payload": {
                        "user_data": {
                            "fullName": item["payload"]["user_data"]["name"],
                            "userAge": item["payload"]["user_data"]["age"],
                            "isAdult": item["payload"]["user_data"]["age"] >= 18,
                        },
                    },
                },
            )
        return transformed

    app = AppSyncEventsResolver()
    app.include_router(router)

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the data should be transformed
    assert "events" in result
    assert len(result["events"]) == 2

    # Check transformation results
    assert result["events"][0]["id"] == "123"
    assert result["events"][0]["payload"]["user_data"]["fullName"] == "John"
    assert result["events"][0]["payload"]["user_data"]["userAge"] == 30
    assert result["events"][0]["payload"]["user_data"]["isAdult"] is True

    assert result["events"][1]["id"] == "456"
    assert result["events"][1]["payload"]["user_data"]["fullName"] == "Jane"
    assert result["events"][1]["payload"]["user_data"]["userAge"] == 16
    assert result["events"][1]["payload"]["user_data"]["isAdult"] is False


def test_empty_events_payload(lambda_context, mock_event):
    """Test handling events with an empty payload."""
    # GIVEN a sample publish event with empty events
    mock_event["events"] = []

    # GIVEN an AppSyncEventsResolver
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*", aggregate=True)
    def handle_events(payload):
        # Should handle empty payload gracefully
        if payload == [{}]:
            return []
        return [{"processed": True} for _ in payload]

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get an empty events list
    assert "events" in result
    assert result["events"] == []


def test_multiple_related_routes_with_precedence(lambda_context, mock_event):
    """Test event routing when multiple paths could match an event."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/products/electronics/phones/123"
    mock_event["events"] = [
        {"id": "123", "payload": {"level": "phones", "data": "product data"}},
    ]

    # GIVEN an AppSyncEventsResolver with multiple related routes
    app = AppSyncEventsResolver()

    # Define resolvers with varying specificity
    @app.on_publish(path="/products/*")
    def general_product_handler(payload):
        return {"level": "general", "data": payload["data"]}

    @app.on_publish(path="/products/electronics/*")
    def electronics_handler(payload):
        return {"level": "electronics", "data": payload["data"]}

    @app.on_publish(path="/products/electronics/phones/*")
    def phones_handler(payload):
        return {"level": "phones", "data": payload["data"]}

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the most specific matching path should be used
    expected_result = {
        "events": [
            {"id": "123", "payload": {"level": "phones", "data": "product data"}},
        ],
    }
    assert result == expected_result


def test_integration_with_external_service(lambda_context, mock_event):
    """Test integration with an external service using mocks."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/orders/process"
    mock_event["events"] = [
        {"id": "123", "payload": {"id": "order-123", "product_id": "prod-456", "quantity": 2}},
    ]

    # Mock an external service
    class MockOrderService:
        @staticmethod
        async def process_order(order_id, product_id, quantity):
            # Simulate processing delay
            await asyncio.sleep(0.01)
            return {
                "order_id": order_id,
                "status": "processed",
                "total_amount": quantity * 10.99,
            }

    order_service = MockOrderService()

    # GIVEN an AppSyncEventsResolver with an async resolver using the service
    app = AppSyncEventsResolver()

    @app.async_on_publish(path="/orders/*")
    async def process_order(payload):
        # Call the external service
        result = await order_service.process_order(
            order_id=payload["id"],
            product_id=payload["product_id"],
            quantity=payload["quantity"],
        )
        return {
            "order_processed": True,
            "order_details": result,
        }

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the order should be processed with the external service
    assert "events" in result
    assert result["events"][0]["payload"]["order_processed"] is True
    assert result["events"][0]["payload"]["order_details"]["order_id"] == "order-123"
    assert result["events"][0]["payload"]["order_details"]["status"] == "processed"
    assert result["events"][0]["payload"]["order_details"]["total_amount"] == 21.98  # 2 * 10.99


def test_complex_resolver_hierarchy(lambda_context, mock_event):
    """Test a complex setup with multiple routers and nested paths."""
    # GIVEN a complex event
    mock_event["info"]["channel"]["path"] = "/api/v1/users/profile/update"
    mock_event["events"] = [
        {"id": "123", "payload": {"profile": {"name": "John Doe", "email": "john@example.com"}}},
    ]

    # GIVEN multiple routers for different API parts
    base_router = Router()
    users_router = Router()
    profiles_router = Router()

    # Add handlers to each router
    @base_router.on_publish(path="/api/*")
    def api_base_handler(payload):
        return {"source": "base", "data": payload}

    @users_router.on_publish(path="/api/v1/users/*")
    def users_handler(payload):
        return {"source": "users", "data": payload}

    @profiles_router.on_publish(path="/api/v1/users/profile/*")
    def profile_handler(payload):
        # Do some profile-specific processing
        return {
            "source": "profiles",
            "updated": True,
            "profile": {
                "fullName": payload["profile"]["name"],
                "email": payload["profile"]["email"],
                "timestamp": "2023-01-01T00:00:00Z",
            },
        }

    # GIVEN an AppSyncEventsResolver with included routers
    app = AppSyncEventsResolver()
    app.include_router(base_router)
    app.include_router(users_router)
    app.include_router(profiles_router)

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the most specific router's handler should be used
    assert "events" in result
    assert result["events"][0]["id"] == "123"
    assert result["events"][0]["payload"]["source"] == "profiles"
    assert result["events"][0]["payload"]["updated"] is True
    assert "fullName" in result["events"][0]["payload"]["profile"]
    assert result["events"][0]["payload"]["profile"]["fullName"] == "John Doe"


def test_warning_behavior_with_no_matching_resolver(lambda_context, mock_event):
    """Test warning behavior when no matching resolver is found."""
    # GIVEN a sample publish event with an unmatched path
    mock_event["info"]["channel"]["path"] = "/unmatched/path"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with a resolver for a different path
    app = AppSyncEventsResolver()

    @app.on_publish(path="/matched/path")
    def test_handler(payload):
        return {"processed": True}

    # WHEN we resolve the event
    # THEN a warning should be generated
    with pytest.warns(UserWarning, match="No resolvers were found for publish operations with path /unmatched/path"):
        result = app.resolve(mock_event, lambda_context)

    # AND the payload should be returned as is
    assert result == {"events": [{"id": "123", "payload": {"data": "test data"}}]}


def test_resolver_precedence_with_exact_match(lambda_context, mock_event):
    """Test that exact path matches have precedence over wildcard matches."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/notifications/system"
    mock_event["events"] = [
        {"id": "123", "payload": {"message": "System notification"}},
    ]

    # GIVEN an AppSyncEventsResolver with both wildcard and exact path resolvers
    app = AppSyncEventsResolver()

    @app.on_publish(path="/notifications/*")
    def wildcard_handler(payload):
        return {"source": "wildcard", "message": payload["message"]}

    @app.on_publish(path="/notifications/system")
    def exact_handler(payload):
        return {"source": "exact", "message": payload["message"]}

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the exact path match should take precedence
    expected_result = {
        "events": [
            {"id": "123", "payload": {"source": "exact", "message": "System notification"}},
        ],
    }
    assert result == expected_result


def test_custom_routing_patterns(lambda_context, mock_event):
    """Test custom routing patterns beyond simple wildcards."""
    # GIVEN events with different path formats
    event1 = deepcopy(mock_event)
    event2 = deepcopy(mock_event)

    event1["info"]["channel"]["path"] = "/users/123/posts/456"
    event1["events"] = [
        {"id": "123", "payload": {"data": "user post data"}},
    ]

    event2["info"]["channel"]["path"] = "/organizations/abc/members/xyz"
    event2["events"] = [
        {"id": "123", "payload": {"data": "organization member data"}},
    ]

    # GIVEN an AppSyncEventsResolver with pattern-based routing
    app = AppSyncEventsResolver()

    # Define resolvers for different entity patterns
    @app.on_publish(path="/users/*")
    def user_resource_handler(payload):
        path = app.current_event.info.channel_path
        segments = path.split("/")
        user_id = segments[2]
        resource_type = segments[3]

        return {"entity_type": "user", "entity_id": user_id, "resource_type": resource_type, "data": payload["data"]}

    @app.on_publish(path="/organizations/*")
    def org_resource_handler(payload):
        path = app.current_event.info.channel_path
        segments = path.split("/")
        org_id = segments[2]
        resource_type = segments[3]

        return {
            "entity_type": "organization",
            "entity_id": org_id,
            "resource_type": resource_type,
            "data": payload["data"],
        }

    # WHEN we resolve the events
    result1 = app.resolve(event1, lambda_context)
    result2 = app.resolve(event2, lambda_context)

    # THEN each event should be handled by the appropriate pattern-based resolver
    assert result1["events"][0]["payload"]["entity_type"] == "user"
    assert result1["events"][0]["payload"]["entity_id"] == "123"
    assert result1["events"][0]["payload"]["resource_type"] == "posts"

    assert result2["events"][0]["payload"]["entity_type"] == "organization"
    assert result2["events"][0]["payload"]["entity_id"] == "abc"
    assert result2["events"][0]["payload"]["resource_type"] == "members"


def test_warning_on_invalid_response_format(lambda_context, mock_event):
    """Test warning generation for invalid response formats."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/default/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
        {"id": "456", "payload": {"data": "more data"}},
    ]

    # GIVEN an AppSyncEventsResolver with an aggregate handler that returns non-list
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*", aggregate=True)
    def invalid_format_handler(payload):
        # Incorrectly return a dict instead of a list
        return {"processed": True, "count": len(payload)}

    # WHEN we resolve the event
    # THEN a warning should be generated about the response format
    with pytest.warns(UserWarning, match="Response must be a list when using aggregate"):
        result = app.resolve(mock_event, lambda_context)

    # The result should still contain what was returned
    assert "events" in result
    assert result["events"]["processed"] is True
    assert result["events"]["count"] == 2


def test_router_and_resolver_clear_context_after_resolution(lambda_context, mock_event):
    """Test that both router and resolver's context are cleared after resolution."""
    # GIVEN a sample publish event
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN a router with context data
    router = Router()
    router.append_context(router_key="router_value")

    @router.on_publish(path="/default/*")
    def router_handler(payload):
        assert router.context["router_key"] == "router_value"
        assert router.context["test_var"] == "app_value"
        return {"processed": True}

    # GIVEN an AppSyncEventsResolver with context data
    app = AppSyncEventsResolver()
    app.append_context(test_var="app_value")

    # Include the router and merge contexts
    app.include_router(router)

    # WHEN we resolve the event
    app.resolve(mock_event, lambda_context)

    # THEN both contexts should be cleared
    assert app.context == {}
    assert router.context == {}


def test_sync_and_async_router_inclusion(lambda_context, mock_event):
    """Test including multiple routers with both sync and async handlers."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/notifications/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"message": "test notification"}},
    ]

    # GIVEN a router with synchronous handlers
    sync_router = Router()

    @sync_router.on_publish(path="/notifications/*")
    def sync_handler(payload):
        return {"sync": True, "message": payload["message"]}

    # GIVEN another router with asynchronous handlers
    async_router = Router()

    @async_router.async_on_publish(path="/notifications/*")
    async def async_handler(event):
        await asyncio.sleep(0.01)
        return {"async": True, "message": event["message"]}

    # GIVEN an AppSyncEventsResolver that includes both routers
    app = AppSyncEventsResolver()
    app.include_router(sync_router)
    app.include_router(async_router)

    # WHEN we resolve the event
    with pytest.warns(UserWarning, match="Both synchronous and asynchronous resolvers found"):
        result = app.resolve(mock_event, lambda_context)

    # THEN the sync handler should take precedence
    expected_result = {
        "events": [
            {"id": "123", "payload": {"sync": True, "message": "test notification"}},
        ],
    }
    assert result == expected_result


def test_aws_lambda_context_availability_in_handlers(lambda_context, mock_event):
    """Test that Lambda context is available in handlers."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/default/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with a handler that uses Lambda context
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def context_aware_handler(payload):
        # Access Lambda context information
        return {
            "processed": True,
            "function_name": app.lambda_context.function_name,
            "request_id": app.lambda_context.aws_request_id,
            "function_arn": app.lambda_context.invoked_function_arn,
            "payload_data": payload["data"],
        }

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN Lambda context information should be included in the result
    assert result["events"][0]["payload"]["function_name"] == lambda_context.function_name
    assert result["events"][0]["payload"]["request_id"] == lambda_context.aws_request_id
    assert result["events"][0]["payload"]["function_arn"] == lambda_context.invoked_function_arn
    assert result["events"][0]["payload"]["payload_data"] == "test data"


def test_router_lambda_context_shared(lambda_context, mock_event):
    """Test that Lambda context is shared with included routers."""
    # GIVEN a sample publish event
    mock_event["info"]["channel"]["path"] = "/router/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN a router with a handler that uses Lambda context
    router = Router()

    @router.on_publish(path="/router/*")
    def router_context_handler(payload):
        # Access Lambda context from the router
        return {
            "from_router": True,
            "function_name": router.lambda_context.function_name,
            "request_id": router.lambda_context.aws_request_id,
            "payload_data": payload["data"],
        }

    # GIVEN an AppSyncEventsResolver that includes the router
    app = AppSyncEventsResolver()
    app.include_router(router)

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the router should have access to the same Lambda context
    assert result["events"][0]["payload"]["from_router"] is True
    assert result["events"][0]["payload"]["function_name"] == lambda_context.function_name
    assert result["events"][0]["payload"]["request_id"] == lambda_context.aws_request_id
    assert result["events"][0]["payload"]["payload_data"] == "test data"


def test_current_event_availability(lambda_context, mock_event):
    """Test that current_event is properly available to handlers."""
    # GIVEN a sample publish event with extra metadata
    mock_event["info"]["channel"]["path"] = "/default/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with a handler that accesses current_event
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def event_aware_handler(payload):
        # Access the full event object for additional context
        return {
            "processed": True,
            "x-forwarded-for": app.current_event.request_headers["x-forwarded-for"],
            "payload_data": payload["data"],
        }

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the handler should have access to the full event information
    assert result["events"][0]["payload"]["processed"] is True
    assert result["events"][0]["payload"]["x-forwarded-for"] == mock_event["request"]["headers"]["x-forwarded-for"]
    assert result["events"][0]["payload"]["payload_data"] == "test data"


def test_router_current_event_shared(lambda_context, mock_event):
    """Test that current_event is shared with included routers."""
    # GIVEN a sample publish event with extra metadata
    mock_event["info"]["channel"]["path"] = "/router/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN a router with a handler that accesses current_event
    router = Router()

    @router.on_publish(path="/router/*")
    def router_event_handler(payload):
        # Access event information from the router
        return {
            "processed": True,
            "x-forwarded-for": app.current_event.request_headers["x-forwarded-for"],
            "payload_data": payload["data"],
        }

    # GIVEN an AppSyncEventsResolver that includes the router
    app = AppSyncEventsResolver()
    app.include_router(router)

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN the router should have access to the same event information
    assert result["events"][0]["payload"]["processed"] is True
    assert result["events"][0]["payload"]["x-forwarded-for"] == mock_event["request"]["headers"]["x-forwarded-for"]
    assert result["events"][0]["payload"]["payload_data"] == "test data"


@pytest.mark.skip(reason="Not implemented yet")
def test_channel_path_normalization(lambda_context, mock_event):
    """Test that channel paths are properly normalized before matching."""
    # GIVEN sample publish events with different path formats
    event1 = deepcopy(mock_event)
    event2 = deepcopy(mock_event)

    event1["info"]["channel"]["path"] = "/test"
    event1["events"] = [
        {"id": "123", "payload": {"data": "data1"}},
    ]

    event2["info"]["channel"]["path"] = "/test/"
    event2["events"] = [
        {"id": "456", "payload": {"data": "data2"}},
    ]

    # GIVEN an AppSyncEventsResolver with a handler
    app = AppSyncEventsResolver()

    @app.on_publish(path="/test")  # Register with path without trailing slash
    def test_handler(payload):
        return {"normalized": True, "data": payload["data"]}

    # WHEN we resolve both events
    result1 = app.resolve(event1, lambda_context)
    result2 = app.resolve(event2, lambda_context)

    # THEN both events should be handled consistently
    expected_result1 = {
        "events": [
            {"id": "123", "payload": {"normalized": True, "data": "data1"}},
        ],
    }
    assert result1 == expected_result1

    # With proper normalization, this should also match
    expected_result2 = {
        "events": [
            {"id": "456", "payload": {"normalized": True, "data": "data2"}},
        ],
    }
    assert result2 == expected_result2


def test_subscribe_event_with_error_handling(lambda_context, mock_event):
    """Test error handling during publish event processing."""
    # GIVEN a sample publish event
    mock_event["info"]["operation"] = "SUBSCRIBE"
    mock_event["info"]["channel"]["path"] = "/default/powertools"
    del mock_event["events"]  # SUBSCRIBE events are not supported

    # GIVEN an AppSyncEventsResolver with a resolver that raises an exception
    app = AppSyncEventsResolver()

    @app.on_subscribe(path="/default/*")
    def test_handler():
        raise ValueError("Test error")

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get an error response
    assert "error" in result
    assert "ValueError - Test error" in result["error"]

def test_subscribe_event_with_valid_return(lambda_context, mock_event):
    """Test error handling during publish event processing."""
    # GIVEN a sample publish event
    mock_event["info"]["operation"] = "SUBSCRIBE"
    mock_event["info"]["channel"]["path"] = "/default/powertools"

    # GIVEN an AppSyncEventsResolver with a resolver that returns ok
    app = AppSyncEventsResolver()

    @app.on_subscribe(path="/default/*")
    def test_handler():
        return 1

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get an error response
    assert result == 1

def test_subscribe_event_with_no_resolver(lambda_context, mock_event):
    """Test error handling during publish event processing."""
    # GIVEN a sample publish event
    mock_event["info"]["operation"] = "SUBSCRIBE"
    mock_event["info"]["channel"]["path"] = "/default/powertools"

    # GIVEN an AppSyncEventsResolver with a resolver that returns ok
    app = AppSyncEventsResolver()

    @app.on_subscribe(path="/test")
    def test_handler():
        return 1

    # WHEN we resolve the event
    result = app.resolve(mock_event, lambda_context)

    # THEN we should get an error response
    assert not result

def test_publish_events_throw_unauthorized_exception(lambda_context, mock_event):
    """Test handling events with an empty payload."""
    # GIVEN a sample publish event with empty events
    mock_event["info"]["operation"] = "PUBLISH"
    mock_event["info"]["channel"]["path"] = "/default/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*", aggregate=True)
    def handle_events(payload):
        raise UnauthorizedException

    # WHEN we resolve the event with unauthorized route
    with pytest.raises(UnauthorizedException):
        app.resolve(mock_event, lambda_context)

def test_subscribe_events_throw_unauthorized_exception(lambda_context, mock_event):
    """Test handling events with an empty payload."""
    # GIVEN a sample publish event with empty events
    mock_event["info"]["operation"] = "SUBSCRIBE"
    mock_event["info"]["channel"]["path"] = "/default/test"

    # GIVEN an AppSyncEventsResolver
    app = AppSyncEventsResolver()

    @app.on_subscribe(path="/default/*")
    def handle_events():
        raise UnauthorizedException

    # WHEN we resolve the event with unauthorized route
    with pytest.raises(UnauthorizedException):
        app.resolve(mock_event, lambda_context)
