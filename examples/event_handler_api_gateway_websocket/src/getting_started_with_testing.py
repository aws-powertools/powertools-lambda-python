import json
from pathlib import Path

from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver


class LambdaContext:
    def __init__(self):
        self.function_name = "test-func"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:eu-west-1:809313241234:function:test-func"
        self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    def get_remaining_time_in_millis(self) -> int:
        return 1000


def test_connect_is_accepted():
    # GIVEN a sample $connect event
    with Path.open(Path("getting_started_with_testing_event.json"), "r") as f:
        event = json.load(f)

    lambda_context = LambdaContext()

    # GIVEN a resolver with a $connect handler
    app = APIGatewayWebSocketResolver()

    @app.on_connect()
    def connect():
        return None

    # WHEN we resolve the event
    result = app.resolve(event, lambda_context)

    # THEN the connection is accepted
    assert result == {"statusCode": 200}
