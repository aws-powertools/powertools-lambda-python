from dataclasses import dataclass
from typing import cast

import app_test_disabling_idempotency_utility
import pytest

from aws_lambda_powertools.utilities.typing import LambdaContext


@dataclass
class FakeLambdaContext:
    function_name: str = "test"
    memory_limit_in_mb: int = 128
    invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
    aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    def get_remaining_time_in_millis(self) -> int:
        return 5


@pytest.fixture
def lambda_context() -> LambdaContext:
    return cast(LambdaContext, FakeLambdaContext())


def test_idempotent_lambda_handler(monkeypatch, lambda_context: LambdaContext):
    # Set POWERTOOLS_IDEMPOTENCY_DISABLED before calling decorated functions
    monkeypatch.setenv("POWERTOOLS_IDEMPOTENCY_DISABLED", 1)

    result = app_test_disabling_idempotency_utility.lambda_handler({}, lambda_context)

    assert result
