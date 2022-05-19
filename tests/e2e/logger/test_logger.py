import boto3
import pytest

from ..utils import helpers


@pytest.fixture(scope="module")
def config():
    return {
        "parameters": {},
        "environment_variables": {
            "MESSAGE": "logger message test",
            "LOG_LEVEL": "INFO",
            "ADDITIONAL_KEY": "extra_info",
        },
    }


@pytest.mark.e2e
def test_basic_lambda_logs_visible(execute_lambda, config):
    # GIVEN
    lambda_arn = execute_lambda["arns"]["basichandlerarn"]
    timestamp = int(execute_lambda["execution_time"].timestamp() * 1000)
    cw_client = boto3.client("logs")

    # WHEN
    filtered_logs = helpers.get_logs(
        lambda_function_name=lambda_arn.split(":")[-1], start_time=timestamp, log_client=cw_client
    )

    # THEN
    assert any(
        log.message == config["environment_variables"]["MESSAGE"]
        and log.level == config["environment_variables"]["LOG_LEVEL"]
        for log in filtered_logs
    )


@pytest.mark.e2e
def test_basic_lambda_no_debug_logs_visible(execute_lambda, config):
    # GIVEN
    lambda_arn = execute_lambda["arns"]["basichandlerarn"]
    timestamp = int(execute_lambda["execution_time"].timestamp() * 1000)
    cw_client = boto3.client("logs")

    # WHEN
    filtered_logs = helpers.get_logs(
        lambda_function_name=lambda_arn.split(":")[-1], start_time=timestamp, log_client=cw_client
    )

    # THEN
    assert not any(
        log.message == config["environment_variables"]["MESSAGE"] and log.level == "DEBUG" for log in filtered_logs
    )


@pytest.mark.e2e
def test_basic_lambda_contextual_data_logged(execute_lambda):
    # GIVEN
    lambda_arn = execute_lambda["arns"]["basichandlerarn"]
    timestamp = int(execute_lambda["execution_time"].timestamp() * 1000)
    cw_client = boto3.client("logs")

    # WHEN
    filtered_logs = helpers.get_logs(
        lambda_function_name=lambda_arn.split(":")[-1], start_time=timestamp, log_client=cw_client
    )

    # THEN
    for log in filtered_logs:
        assert (
            log.xray_trace_id
            and log.function_request_id
            and log.function_arn
            and log.function_memory_size
            and log.function_name
            and str(log.cold_start)
        )


@pytest.mark.e2e
def test_basic_lambda_additional_key_persistence_basic_lambda(execute_lambda, config):
    # GIVEN

    lambda_arn = execute_lambda["arns"]["basichandlerarn"]
    timestamp = int(execute_lambda["execution_time"].timestamp() * 1000)
    cw_client = boto3.client("logs")

    # WHEN
    filtered_logs = helpers.get_logs(
        lambda_function_name=lambda_arn.split(":")[-1], start_time=timestamp, log_client=cw_client
    )

    # THEN
    assert any(
        log.extra_info
        and log.message == config["environment_variables"]["MESSAGE"]
        and log.level == config["environment_variables"]["LOG_LEVEL"]
        for log in filtered_logs
    )


@pytest.mark.e2e
def test_basic_lambda_empty_event_logged(execute_lambda):

    # GIVEN
    lambda_arn = execute_lambda["arns"]["basichandlerarn"]
    timestamp = int(execute_lambda["execution_time"].timestamp() * 1000)
    cw_client = boto3.client("logs")

    # WHEN
    filtered_logs = helpers.get_logs(
        lambda_function_name=lambda_arn.split(":")[-1], start_time=timestamp, log_client=cw_client
    )

    # THEN
    assert any(log.message == {} for log in filtered_logs)


@pytest.mark.e2e
def test_no_context_lambda_contextual_data_not_logged(execute_lambda):

    # GIVEN
    lambda_arn = execute_lambda["arns"]["nocontexthandlerarn"]
    timestamp = int(execute_lambda["execution_time"].timestamp() * 1000)
    cw_client = boto3.client("logs")

    # WHEN
    filtered_logs = helpers.get_logs(
        lambda_function_name=lambda_arn.split(":")[-1], start_time=timestamp, log_client=cw_client
    )

    # THEN
    assert not any(
        (
            log.xray_trace_id
            and log.function_request_id
            and log.function_arn
            and log.function_memory_size
            and log.function_name
            and str(log.cold_start)
        )
        for log in filtered_logs
    )


@pytest.mark.e2e
def test_no_context_lambda_event_not_logged(execute_lambda):

    # GIVEN
    lambda_arn = execute_lambda["arns"]["nocontexthandlerarn"]
    timestamp = int(execute_lambda["execution_time"].timestamp() * 1000)
    cw_client = boto3.client("logs")

    # WHEN
    filtered_logs = helpers.get_logs(
        lambda_function_name=lambda_arn.split(":")[-1], start_time=timestamp, log_client=cw_client
    )

    # THEN
    assert not any(log.message == {} for log in filtered_logs)


### Add tests for cold start and non-cold start executions
### Test errors
### Test child loggers
