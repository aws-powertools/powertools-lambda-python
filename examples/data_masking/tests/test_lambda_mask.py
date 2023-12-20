from dataclasses import dataclass

import pytest
import test_lambda_mask


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

        def get_remaining_time_in_millis(self) -> int:
            return 5

    return LambdaContext()


def test_encrypt_lambda(lambda_context):
    # GIVEN: A sample event for testing
    event = {"testkey": "testvalue"}

    # WHEN: Invoking the lambda_handler function with the sample event and Lambda context
    result = test_lambda_mask.lambda_handler(event, lambda_context)

    # THEN: Assert that the result matches the expected output
    assert result == {"testkey": "*****"}
