import json
from pathlib import Path

from aws_lambda_powertools.event_handler import AppSyncEventsResolver


class LambdaContext:
    def __init__(self):
        self.function_name = "test-func"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:eu-west-1:809313241234:function:test-func"
        self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    def get_remaining_time_in_millis(self) -> int:
        return 1000


def test_subscribe_event_with_valid_return():
    """Test error handling during publish event processing."""
    # GIVEN a sample publish event
    with Path.open("getting_started_with_testing_publish_event.json", "r") as f:
        event = json.load(f)

    lambda_context = LambdaContext()

    # GIVEN an AppSyncEventsResolver with a resolver that returns ok
    app = AppSyncEventsResolver()

    @app.on_subscribe(path="/default/*")
    def test_handler():
        pass

    # WHEN we resolve the event
    result = app.resolve(event, lambda_context)

    # THEN we should return None because subscribe always must return None
    assert result is None
