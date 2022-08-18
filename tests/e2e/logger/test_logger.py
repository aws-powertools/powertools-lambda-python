import boto3
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
    cw_client = boto3.client("logs")
    required_keys = (
        "xray_trace_id",
        "function_request_id",
        "function_arn",
        "function_memory_size",
        "function_name",
        "cold_start",
    )

    # WHEN
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn)
    filtered_logs = data_fetcher.get_logs(
        lambda_function_name=basic_handler_fn, start_time=int(execution_time.timestamp()), log_client=cw_client
    )

    # THEN
    assert all(keys in logs.dict(exclude_unset=True) for logs in filtered_logs for keys in required_keys)
