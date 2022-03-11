from collections import namedtuple

import pytest


@pytest.fixture
def lambda_context():
    lambda_context = {
        "function_name": "test",
        "memory_limit_in_mb": 128,
        "invoked_function_arn": "arn:aws:lambda:eu-west-1:809313241:function:test",
        "aws_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
    }

    return namedtuple("LambdaContext", lambda_context.keys())(*lambda_context.values())


def test_lambda_handler(lambda_context):
    test_event = {"test": "event"}

    # this will now have a Context object populated
    your_lambda_handler(test_event, lambda_context)
