import json
from uuid import uuid4

import pytest

from tests.e2e.utils import data_fetcher


@pytest.fixture
def basic_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandler", "")


@pytest.fixture
def basic_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandlerArn", "")


def test_basic_lambda_logs_visible(basic_handler_fn, basic_handler_fn_arn):
    # GIVEN
    required_keys = (
        "xray_trace_id",
        "function_request_id",
        "function_arn",
        "function_memory_size",
        "function_name",
        "cold_start",
    )
    message = "logs should be visible with default settings"
    additional_keys = {"order_id": f"{uuid4()}"}
    payload = json.dumps({"message": message, "append_keys": additional_keys})

    # WHEN
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=payload)
    filtered_logs = data_fetcher.get_logs(function_name=basic_handler_fn, start_time=execution_time)

    # THEN
    assert all(keys in logs.dict(exclude_unset=True) for logs in filtered_logs for keys in required_keys)
    assert any(getattr(logs, "order_id", False) for logs in filtered_logs)
