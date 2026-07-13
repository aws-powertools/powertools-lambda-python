import json
from copy import deepcopy

import pytest

from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
from aws_lambda_powertools.event_handler.api_gateway_websocket import Router
from aws_lambda_powertools.event_handler.api_gateway_websocket._registry import RouteRegistry
from aws_lambda_powertools.utilities.data_classes import APIGatewayWebSocketEvent
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
    return LambdaContext()


@pytest.fixture(scope="module")
def connect_event():
    return load_event("apiGatewayWebSocketApiConnect.json")


@pytest.fixture(scope="module")
def disconnect_event():
    return load_event("apiGatewayWebSocketApiDisconnect.json")


@pytest.fixture(scope="module")
def message_event():
    return load_event("apiGatewayWebSocketApiMessage.json")


def test_connect_route_dispatch(connect_event, lambda_context):
    # GIVEN a resolver with a $connect handler returning None
    app = APIGatewayWebSocketResolver()
    invocations = []

    @app.on_connect()
    def connect():
        invocations.append(app.current_event.request_context.connection_id)

    # WHEN a $connect event is resolved
    result = app.resolve(connect_event, lambda_context)

    # THEN the handler runs and None normalizes to a bare 200 (accept the connection)
    assert invocations == [connect_event["requestContext"]["connectionId"]]
    assert result == {"statusCode": 200}


def test_disconnect_route_dispatch(disconnect_event, lambda_context):
    # GIVEN a resolver with a $disconnect handler reading the disconnect details
    app = APIGatewayWebSocketResolver()
    captured = {}

    @app.on_disconnect()
    def disconnect():
        captured["status_code"] = app.current_event.request_context.disconnect_status_code
        captured["reason"] = app.current_event.request_context.disconnect_reason

    # WHEN a $disconnect event is resolved
    result = app.resolve(disconnect_event, lambda_context)

    # THEN the handler sees the close details from the event
    assert result == {"statusCode": 200}
    assert captured["status_code"] == disconnect_event["requestContext"]["disconnectStatusCode"]
    assert captured["reason"] == disconnect_event["requestContext"]["disconnectReason"]


def test_default_route_reads_json_body(message_event, lambda_context):
    # GIVEN a $default handler and a message event with a JSON body
    event = deepcopy(message_event)
    event["requestContext"]["routeKey"] = "$default"
    app = APIGatewayWebSocketResolver()

    @app.on_default()
    def default():
        return {"received": app.current_event.json_body["message"]}

    # WHEN the event is resolved
    result = app.resolve(event, lambda_context)

    # THEN the handler reads the parsed body and the dict is JSON-serialized
    assert result == {"statusCode": 200, "body": json.dumps({"received": "Hello from client"}, separators=(",", ":"))}


def test_custom_route_key_dispatch(message_event, lambda_context):
    # GIVEN a handler registered for a custom route key
    event = deepcopy(message_event)
    event["requestContext"]["routeKey"] = "orderUpdate"
    app = APIGatewayWebSocketResolver()

    @app.route("orderUpdate")
    def order_update():
        return "order received"

    # WHEN an event with that route key is resolved
    result = app.resolve(event, lambda_context)

    # THEN the custom route handler is dispatched and str returns pass through as body
    assert result == {"statusCode": 200, "body": "order received"}


@pytest.mark.parametrize(
    ("handler_return", "expected"),
    [
        (None, {"statusCode": 200}),
        ("plain text", {"statusCode": 200, "body": "plain text"}),
        ({"statusCode": 999}, {"statusCode": 200, "body": '{"statusCode":999}'}),
        (["a", "b"], {"statusCode": 200, "body": '["a","b"]'}),
        ((None, 401), {"statusCode": 401}),
        (({"reason": "full"}, 503), {"statusCode": 503, "body": '{"reason":"full"}'}),
        (("denied", 403), {"statusCode": 403, "body": "denied"}),
    ],
    ids=["none", "str", "dict-with-statusCode-key-is-body", "list", "tuple-none", "tuple-dict", "tuple-str"],
)
def test_return_value_normalization(connect_event, lambda_context, handler_return, expected):
    # GIVEN a handler returning each supported shape
    app = APIGatewayWebSocketResolver()

    @app.on_connect()
    def connect():
        return handler_return

    # WHEN the event is resolved
    result = app.resolve(connect_event, lambda_context)

    # THEN the response matches the normalization table exactly
    assert result == expected


def test_unknown_route_key_warns_and_returns_400(message_event, lambda_context):
    # GIVEN a resolver with no handler for the event's route key
    app = APIGatewayWebSocketResolver()

    @app.on_connect()
    def connect():
        return None

    # WHEN the event is resolved
    with pytest.warns(PowertoolsUserWarning, match="No route handler registered for route key `chat`"):
        result = app.resolve(message_event, lambda_context)

    # THEN a bare 400 is returned
    assert result == {"statusCode": 400}


def test_duplicate_route_registration_warns_last_wins(connect_event, lambda_context):
    # GIVEN two handlers registered for the same route key
    app = APIGatewayWebSocketResolver()

    @app.on_connect()
    def first():
        return "first"

    with pytest.warns(PowertoolsUserWarning, match="already registered for route key `\\$connect`"):

        @app.on_connect()
        def second():
            return "second"

    # WHEN the event is resolved
    result = app.resolve(connect_event, lambda_context)

    # THEN the last registration wins
    assert result == {"statusCode": 200, "body": "second"}


def test_empty_route_key_registration_warns_and_skips(connect_event, lambda_context):
    # GIVEN a handler registered with an empty route key
    app = APIGatewayWebSocketResolver()

    with pytest.warns(PowertoolsUserWarning, match="route key registered for `handler` is empty"):

        @app.route("")
        def handler():
            return None

    # THEN the function is returned undecorated and nothing is registered
    assert handler() is None
    assert app._route_registry.routes == {}


def test_current_event_and_lambda_context(connect_event, lambda_context):
    # GIVEN a resolver and a handler inspecting the event and context
    app = APIGatewayWebSocketResolver()
    captured = {}

    @app.on_connect()
    def connect():
        captured["event"] = app.current_event
        captured["context"] = app.lambda_context

    # WHEN resolving a raw dict event
    app.resolve(connect_event, lambda_context)

    # THEN the event is wrapped in the data class and the context is set
    assert isinstance(captured["event"], APIGatewayWebSocketEvent)
    assert captured["event"].request_context.route_key == "$connect"
    assert captured["context"] is lambda_context


def test_already_wrapped_event_is_not_rewrapped(connect_event, lambda_context):
    # GIVEN an event already wrapped in the data class
    wrapped = APIGatewayWebSocketEvent(connect_event)
    app = APIGatewayWebSocketResolver()
    captured = {}

    @app.on_connect()
    def connect():
        captured["event"] = app.current_event

    # WHEN it is resolved
    result = app.resolve(wrapped, lambda_context)

    # THEN the same instance is used and dispatch works
    assert captured["event"] is wrapped
    assert result == {"statusCode": 200}


def test_unhandled_exception_returns_bare_500(connect_event, lambda_context):
    # GIVEN a handler raising an exception with no registered handler
    app = APIGatewayWebSocketResolver()
    secret_message = "sensitive detail about the failure"

    @app.on_connect()
    def connect():
        raise RuntimeError(secret_message)

    # WHEN the event is resolved
    result = app.resolve(connect_event, lambda_context)

    # THEN a bare 500 is returned with no exception details anywhere in the response
    assert result == {"statusCode": 500}
    serialized = json.dumps(result)
    assert secret_message not in serialized
    assert "RuntimeError" not in serialized
    assert "Traceback" not in serialized


def test_registered_exception_handler_response_is_normalized(connect_event, lambda_context):
    # GIVEN an exception handler registered for ValueError
    app = APIGatewayWebSocketResolver()

    @app.exception_handler(ValueError)
    def handle_value_error(exc: ValueError):
        return {"error": str(exc)}, 400

    @app.on_connect()
    def connect():
        raise ValueError("bad input")

    # WHEN the event is resolved
    result = app.resolve(connect_event, lambda_context)

    # THEN the handler's return value goes through the same normalization
    assert result == {"statusCode": 400, "body": '{"error":"bad input"}'}


def test_exception_handler_lookup_respects_inheritance(connect_event, lambda_context):
    # GIVEN a handler registered for a base exception class
    class OrderError(Exception): ...

    class OrderNotFoundError(OrderError): ...

    app = APIGatewayWebSocketResolver()

    @app.exception_handler(OrderError)
    def handle_order_error(exc: OrderError):
        return None, 404

    @app.on_connect()
    def connect():
        raise OrderNotFoundError("order 123 not found")

    # WHEN a subclass of the registered exception is raised
    result = app.resolve(connect_event, lambda_context)

    # THEN the base class handler is used
    assert result == {"statusCode": 404}


def test_disconnect_dispatches_even_when_connect_was_rejected(connect_event, disconnect_event, lambda_context):
    # GIVEN a resolver whose $connect handler rejects the connection
    app = APIGatewayWebSocketResolver()
    dispatched = []

    @app.on_connect()
    def connect():
        dispatched.append("$connect")
        return None, 401

    @app.on_disconnect()
    def disconnect():
        dispatched.append("$disconnect")

    # WHEN $connect is rejected and API Gateway later delivers $disconnect anyway
    connect_result = app.resolve(connect_event, lambda_context)
    disconnect_result = app.resolve(disconnect_event, lambda_context)

    # THEN the resolver keeps no per-connection state and dispatches both
    assert connect_result == {"statusCode": 401}
    assert disconnect_result == {"statusCode": 200}
    assert dispatched == ["$connect", "$disconnect"]


def test_resolver_is_callable_as_lambda_handler(connect_event, lambda_context):
    # GIVEN a resolver with a $connect handler
    app = APIGatewayWebSocketResolver()

    @app.on_connect()
    def connect():
        return None

    # WHEN the resolver instance itself is used as the Lambda handler
    result = app(connect_event, lambda_context)

    # THEN it resolves the event
    assert result == {"statusCode": 200}


def test_append_context_visible_in_handler_and_cleared_after_resolve(connect_event, lambda_context):
    # GIVEN context appended before resolution
    app = APIGatewayWebSocketResolver()
    app.append_context(tenant_id="tenant-a")
    captured = {}

    @app.on_connect()
    def connect():
        captured["tenant_id"] = app.context.get("tenant_id")

    # WHEN the event is resolved
    app.resolve(connect_event, lambda_context)

    # THEN the handler sees the context and it is cleared afterwards
    assert captured["tenant_id"] == "tenant-a"
    assert app.context == {}


def test_malformed_event_returns_bare_500(lambda_context):
    # GIVEN an event missing requestContext entirely
    app = APIGatewayWebSocketResolver()

    @app.on_connect()
    def connect():
        return None

    # WHEN the event is resolved
    result = app.resolve({}, lambda_context)

    # THEN the resolver returns a bare 500 with no exception details
    assert result == {"statusCode": 500}


def test_exception_handler_raising_returns_bare_500(connect_event, lambda_context):
    # GIVEN an exception handler that itself raises
    app = APIGatewayWebSocketResolver()
    secret_message = "sensitive detail about the failure"

    @app.exception_handler(ValueError)
    def handle_value_error(exc: ValueError):
        raise RuntimeError(secret_message)

    @app.on_connect()
    def connect():
        raise ValueError("bad input")

    # WHEN the event is resolved
    result = app.resolve(connect_event, lambda_context)

    # THEN a bare 500 is returned with no exception details
    assert result == {"statusCode": 500}
    assert secret_message not in json.dumps(result)


def test_router_exception_handler_registration():
    # GIVEN a Router with exception handlers registered for a single and a list of types
    router = Router()

    @router.exception_handler(ValueError)
    def handle_value_error(exc: ValueError): ...

    @router.exception_handler([KeyError, TypeError])
    def handle_lookup_errors(exc: Exception): ...

    # THEN the handlers are stored for merging via include_router
    assert router._exception_handlers[ValueError] is handle_value_error
    assert router._exception_handlers[KeyError] is handle_lookup_errors
    assert router._exception_handlers[TypeError] is handle_lookup_errors


def test_route_registry_merge():
    # GIVEN two registries with registered routes
    first = RouteRegistry()
    second = RouteRegistry()

    @first.register("$connect")
    def connect(): ...

    @second.register("orderUpdate")
    def order_update(): ...

    # WHEN one registry is merged into the other
    first.merge(second)

    # THEN both routes are found in the merged registry
    assert first.find_route("$connect")["func"] is connect
    assert first.find_route("orderUpdate")["func"] is order_update


def test_duplicate_disconnect_delivery_dispatches_both(disconnect_event, lambda_context):
    # GIVEN a resolver with a $disconnect handler ($disconnect delivery is at-least-once in production)
    app = APIGatewayWebSocketResolver()
    dispatched = []

    @app.on_disconnect()
    def disconnect():
        dispatched.append(app.current_event.request_context.connection_id)

    # WHEN the same $disconnect event is delivered twice
    first = app.resolve(disconnect_event, lambda_context)
    second = app.resolve(disconnect_event, lambda_context)

    # THEN both deliveries dispatch to the handler and succeed
    assert first == {"statusCode": 200}
    assert second == {"statusCode": 200}
    assert dispatched == [disconnect_event["requestContext"]["connectionId"]] * 2


def test_system_route_key_registrable_via_route_primitive(disconnect_event, lambda_context):
    # GIVEN a $disconnect handler registered via the route() primitive instead of on_disconnect()
    app = APIGatewayWebSocketResolver()
    dispatched = []

    @app.route("$disconnect")
    def disconnect():
        dispatched.append(app.current_event.request_context.route_key)

    # WHEN a $disconnect event is resolved
    result = app.resolve(disconnect_event, lambda_context)

    # THEN it dispatches identically to the sugar decorator
    assert result == {"statusCode": 200}
    assert dispatched == ["$disconnect"]
