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
    message = "logs should be visible with default settings"
    custom_key = "order_id"
    additional_keys = {custom_key: f"{uuid4()}"}
    payload = json.dumps({"message": message, "append_keys": additional_keys})

    # WHEN
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=payload)
    logs = data_fetcher.get_logs(function_name=basic_handler_fn, start_time=execution_time)

    # THEN
    assert len(logs) == 1
    assert len(logs.get_cold_start_log()) == 1
    assert len(logs.get_log(key=custom_key)) == 1
    assert logs.have_logger_context_keys() is True
