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


# test on combination of tz,datefmt params
@pytest.mark.xdist_group(name="logger")
@pytest.mark.parametrize("tz", ["US/Eastern", "UTC", "Asia/Shanghai"])
@pytest.mark.parametrize("datefmt", ["%z", None])
def test_lambda_tz_with_utc(tz_handler_fn, tz_handler_fn_arn, tz, datefmt):
    # GIVEN UTC=True
    utc = True
    payload = json.dumps({"utc": utc, "tz": tz, "datefmt": datefmt})

    # WHEN invoking sample hander using combination of timezone and date format
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=tz_handler_fn_arn, payload=payload)
    data_fetcher.get_lambda_response(lambda_arn=tz_handler_fn_arn, payload=payload)

    # get log with matching service id from logger in sample handler
    logs = data_fetcher.get_logs(
        function_name=tz_handler_fn,
        start_time=execution_time,
        minimum_log_entries=1,
        filter_expression='{ $.service = "' + f"{utc}-{datefmt}-{tz}" + '" }',
    )
    result_list = logs.logs

    assert len(result_list) > 0
    result = result_list[0]

    # Then lambda handler use gmt converter, timezone always in UTC
    assert result.message == "gmtime_converter"
    assert result.timestamp[-5:] == "+0000"


# test on combination of tz,datefmt params on
@pytest.mark.xdist_group(name="logger")
@pytest.mark.parametrize("tz", ["US/Eastern", "UTC", "Asia/Shanghai"])
@pytest.mark.parametrize("datefmt", ["%z", None])
def test_lambda_tz_without_utc(tz_handler_fn, tz_handler_fn_arn, tz, datefmt):
    # GIVEN UTC=False
    utc = False
    payload = json.dumps({"utc": utc, "tz": tz, "datefmt": datefmt})

    # WHEN invoking sample handler using combination of timezone and date format
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=tz_handler_fn_arn, payload=payload)
    data_fetcher.get_lambda_response(lambda_arn=tz_handler_fn_arn, payload=payload)

    # get log with matching service id from logger in sample handler
    logs = data_fetcher.get_logs(
        function_name=tz_handler_fn,
        start_time=execution_time,
        minimum_log_entries=1,
        filter_expression='{ $.service = "' + f"{utc}-{datefmt}-{tz}" + '" }',
    )
    result_list = logs.logs

    assert len(result_list) > 0
    result = result_list[0]

    # then Lambda handler use localtime converter
    assert result.message == "localtime_converter"

    # set Tz and assert result is the same as lambda output
    os.environ["TZ"] = tz
    time.tzset()
    assert result.timestamp[-5:] == time.strftime("%z", time.localtime())
