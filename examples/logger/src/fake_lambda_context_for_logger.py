from dataclasses import dataclass

import fake_lambda_context_for_logger_module  # sample module for completeness
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
    test_event = {"test": "event"}
    fake_lambda_context_for_logger_module.handler(test_event, lambda_context)
