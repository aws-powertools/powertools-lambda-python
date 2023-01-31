import json
from uuid import uuid4

import pytest

from aws_lambda_powertools.shared.constants import LOGGER_LAMBDA_CONTEXT_KEYS
from tests.e2e.utils import data_fetcher


@pytest.fixture
def basic_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandler", "")


@pytest.fixture
def basic_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandlerArn", "")


@pytest.mark.xdist_group(name="logger")
def test_basic_lambda_logs_visible(basic_handler_fn, basic_handler_fn_arn):
    # GIVEN
    message = "logs should be visible with default settings"
    custom_key = "order_id"
    additional_keys = {custom_key: f"{uuid4()}"}
    payload = json.dumps({"message": message, "append_keys": additional_keys})

    # WHEN
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=payload)
    data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=payload)

    # THEN
    logs = data_fetcher.get_logs(function_name=basic_handler_fn, start_time=execution_time, minimum_log_entries=2)

    assert len(logs) == 2
    assert len(logs.get_cold_start_log()) == 1
    assert len(logs.get_log(key=custom_key)) == 2
    assert logs.have_keys(*LOGGER_LAMBDA_CONTEXT_KEYS) is True
