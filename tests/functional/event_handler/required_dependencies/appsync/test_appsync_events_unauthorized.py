import pytest

from aws_lambda_powertools.event_handler import AppSyncEventsResolver
from aws_lambda_powertools.event_handler.events_appsync.exceptions import UnauthorizedException
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
def mock_event():
    return load_event("appSyncEventsEvent.json")


def test_publish_events_throw_unauthorized_exception_without_aggregate(lambda_context, mock_event):
    """UnauthorizedException raised in a per-event resolver must not be swallowed.

    When aggregate=False, each event is handled independently and any other exception is
    turned into a per-event error payload. Authorization failures are the exception: they
    must fail the whole request, otherwise a denied caller receives a successful response.
    """
    # GIVEN a publish event with a single event
    mock_event["info"]["operation"] = "PUBLISH"
    mock_event["info"]["channel"]["path"] = "/default/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with a per-event resolver that denies access
    app = AppSyncEventsResolver()

    @app.on_publish(path="/default/*")
    def handle_events(payload):
        raise UnauthorizedException

    # WHEN we resolve the event
    # THEN the exception must propagate to the caller
    with pytest.raises(UnauthorizedException):
        app.resolve(mock_event, lambda_context)


def test_async_publish_events_throw_unauthorized_exception_without_aggregate(lambda_context, mock_event):
    """UnauthorizedException raised in an async per-event resolver must not be swallowed."""
    # GIVEN a publish event with a single event
    mock_event["info"]["operation"] = "PUBLISH"
    mock_event["info"]["channel"]["path"] = "/default/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
    ]

    # GIVEN an AppSyncEventsResolver with an async per-event resolver that denies access
    app = AppSyncEventsResolver()

    @app.async_on_publish(path="/default/*")
    async def handle_events(payload):
        raise UnauthorizedException

    # WHEN we resolve the event
    # THEN the exception must propagate to the caller
    with pytest.raises(UnauthorizedException):
        app.resolve(mock_event, lambda_context)


def test_publish_events_throw_unauthorized_exception_with_multiple_events(lambda_context, mock_event):
    """A single denied event must fail the whole batch, even when other events succeed."""
    # GIVEN a publish event with two events
    mock_event["info"]["operation"] = "PUBLISH"
    mock_event["info"]["channel"]["path"] = "/default/test"
    mock_event["events"] = [
        {"id": "123", "payload": {"data": "test data"}},
        {"id": "456", "payload": {"data": "more test data"}},
    ]

    # GIVEN an AppSyncEventsResolver that allows the first event and denies the second one
    app = AppSyncEventsResolver()
    calls = []

    @app.on_publish(path="/default/*")
    def handle_events(payload):
        calls.append(payload)
        if len(calls) == 2:
            raise UnauthorizedException
        return {"processed": True}

    # WHEN we resolve the event
    # THEN the exception must propagate to the caller
    with pytest.raises(UnauthorizedException):
        app.resolve(mock_event, lambda_context)
