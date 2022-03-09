from dataclasses import dataclass

import app
import pytest


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    return LambdaContext()


def test_lambda_handler(lambda_context):
    minimal_event = {
        "path": "/hello",
        "httpMethod": "GET",
        "requestContext": {
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",  # correlation ID
        },
    }

    app.lambda_handler(minimal_event, lambda_context)
