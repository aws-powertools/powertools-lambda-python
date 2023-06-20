from dataclasses import dataclass
from unittest.mock import MagicMock

import app_test_io_operations
import pytest


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


def test_idempotent_lambda(lambda_context):
    mock_client = MagicMock()
    app_test_io_operations.persistence_layer.client = mock_client
    result = app_test_io_operations.handler({"testkey": "testvalue"}, lambda_context)
    mock_client.put_item.assert_called()
    assert result
