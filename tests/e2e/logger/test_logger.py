import datetime
import os

import boto3
import pytest

from .. import utils

dirname = os.path.dirname(__file__)


@pytest.fixture(scope="module")
def config():
    return {"MESSAGE": "logger message test", "LOG_LEVEL": "INFO", "ADDITIONAL_KEY": "extra_info"}


@pytest.fixture(scope="module")
def deploy_basic_lambda(deploy_infrastructure, config):
    lambda_arn = deploy_infrastructure(
        handler_filename=f"{dirname}/handlers/basic_handler.py",
        environment_variables=config,
    )
    epoch = int(datetime.datetime.now().timestamp() * 1000)
    result = utils.trigger_lambda(lambda_arn=lambda_arn)

    assert result["Payload"].read() == b'"success"'
    return lambda_arn, epoch


@pytest.fixture(scope="module")
def deploy_no_context_lambda(deploy_infrastructure, config):
    lambda_arn = deploy_infrastructure(
        handler_filename=f"{dirname}/handlers/no_context_handler.py", environment_variables=config
    )

    epoch = int(datetime.datetime.now().timestamp() * 1000)
    result = utils.trigger_lambda(lambda_arn=lambda_arn)

    assert result["Payload"].read() == b'"success"'
    return lambda_arn, epoch


@pytest.mark.e2e
def test_basic_lambda_logs_visible(deploy_basic_lambda, config):
    filtered_logs = utils.get_logs(
        start_time=deploy_basic_lambda[1],
        lambda_function_name=deploy_basic_lambda[0].split(":")[-1],
        log_client=boto3.client("logs"),
    )
    assert any(log.message == config["MESSAGE"] and log.level == config["LOG_LEVEL"] for log in filtered_logs)


@pytest.mark.e2e
def test_basic_lambda_no_debug_logs_visible(deploy_basic_lambda, config):
    filtered_logs = utils.get_logs(
        start_time=deploy_basic_lambda[1],
        lambda_function_name=deploy_basic_lambda[0].split(":")[-1],
        log_client=boto3.client("logs"),
    )
    assert not any(log.message == config["MESSAGE"] and log.level == "DEBUG" for log in filtered_logs)


@pytest.mark.e2e
def test_basic_lambda_contextual_data_logged(deploy_basic_lambda):
    filtered_logs = utils.get_logs(
        start_time=deploy_basic_lambda[1],
        lambda_function_name=deploy_basic_lambda[0].split(":")[-1],
        log_client=boto3.client("logs"),
    )
    assert all(
        (
            log.xray_trace_id
            and log.function_request_id
            and log.function_arn
            and log.function_memory_size
            and log.function_name
            and log.cold_start
        )
        for log in filtered_logs
    )


@pytest.mark.e2e
def test_basic_lambda_additional_key_persistence_basic_lambda(deploy_basic_lambda, config):
    filtered_logs = utils.get_logs(
        start_time=deploy_basic_lambda[1],
        lambda_function_name=deploy_basic_lambda[0].split(":")[-1],
        log_client=boto3.client("logs"),
    )
    assert any(
        log.extra_info and log.message == config["MESSAGE"] and log.level == config["LOG_LEVEL"]
        for log in filtered_logs
    )


@pytest.mark.e2e
def test_basic_lambda_empty_event_logged(deploy_basic_lambda):
    filtered_logs = utils.get_logs(
        start_time=deploy_basic_lambda[1],
        lambda_function_name=deploy_basic_lambda[0].split(":")[-1],
        log_client=boto3.client("logs"),
    )
    assert any(log.message == {} for log in filtered_logs)


# Deploy new lambda using cdk hotswap mechanism
@pytest.mark.e2e
def test_no_context_lambda_contextual_data_not_logged(deploy_no_context_lambda):
    filtered_logs = utils.get_logs(
        start_time=deploy_no_context_lambda[1],
        lambda_function_name=deploy_no_context_lambda[0].split(":")[-1],
        log_client=boto3.client("logs"),
    )
    assert not any(
        (
            log.xray_trace_id
            and log.function_request_id
            and log.function_arn
            and log.function_memory_size
            and log.function_name
            and log.cold_start
        )
        for log in filtered_logs
    )


@pytest.mark.e2e
def test_no_context_lambda_event_not_logged(deploy_no_context_lambda):
    filtered_logs = utils.get_logs(
        start_time=deploy_no_context_lambda[1],
        lambda_function_name=deploy_no_context_lambda[0].split(":")[-1],
        log_client=boto3.client("logs"),
    )
    assert not any(log.message == {} for log in filtered_logs)


### Add tests for cold start and non-cold start executions
### Test errors
### Test child loggers
