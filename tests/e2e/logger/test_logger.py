import json
import os
import time
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


@pytest.fixture
def tz_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("TzHandler", "")


@pytest.fixture
def tz_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("TzHandlerArn", "")


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


# test on combination of utc,tz,datefmt params
@pytest.mark.xdist_group(name="logger")
@pytest.mark.parametrize("utc", [False, True])
@pytest.mark.parametrize("tz", ["US/Eastern", "UTC", "Asia/Shanghai"])
@pytest.mark.parametrize("datefmt", ["%z", None])
def test_lambda_tz(tz_handler_fn, tz_handler_fn_arn, utc, tz, datefmt):
    # GIVEN
    payload = json.dumps({"utc": utc, "tz": tz, "datefmt": datefmt})

    # WHEN
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=tz_handler_fn_arn, payload=payload)
    data_fetcher.get_lambda_response(lambda_arn=tz_handler_fn_arn, payload=payload)

    # THEN
    logs = data_fetcher.get_logs(
        function_name=tz_handler_fn,
        start_time=execution_time,
        minimum_log_entries=1,
        filter_expression='{ $.service = "' + f"{utc}-{datefmt}-{tz}" + '" }',
    )
    result_list = logs.logs

    assert len(result_list) > 0
    result = result_list[0]

    # When UTC
    if utc:
        # then use gmt converter
        assert result.message == "gmtime_converter"
    # When not UTC
    else:
        # then use local time converter
        assert result.message == "localtime_converter"

    if utc:
        assert result.timestamp[-5:] == "+0000"
    else:
        os.environ["TZ"] = tz
        time.tzset()
        assert result.timestamp[-5:] == time.strftime("%z", time.localtime())

    print(result)
