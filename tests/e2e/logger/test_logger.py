import datetime
import os
from functools import lru_cache

import boto3
import pytest

from .. import utils

dirname = os.path.dirname(__file__)


@pytest.fixture(scope="module")
def config():
    return {"MESSAGE": "logger message test", "LOG_LEVEL": "INFO", "ADDITIONAL_KEY": "extra_info"}


@pytest.fixture(scope="module")
def deploy_lambdas(deploy, config):
    handlers_dir = f"{dirname}/handlers/"

    lambda_arns = deploy(
        handlers_name=utils.find_handlers(handlers_dir),
        handlers_dir=handlers_dir,
        environment_variables=config,
    )

    for name, arn in lambda_arns.items():
        utils.trigger_lambda(lambda_arn=arn)
        print(f"lambda {name} triggered")
    return lambda_arns


@pytest.fixture(scope="module")
def trigger_lambdas(deploy_lambdas):
    for name, arn in deploy_lambdas.items():
        utils.trigger_lambda(lambda_arn=arn)
        print(f"lambda {name} triggered")


@lru_cache(maxsize=10, typed=False)
def fetch_logs(lambda_arn):
    start_time = int(datetime.datetime.now().timestamp() * 1000)
    result = utils.trigger_lambda(lambda_arn=lambda_arn)

    filtered_logs = utils.get_logs(
        start_time=start_time,
        lambda_function_name=lambda_arn.split(":")[-1],
        log_client=boto3.client("logs"),
    )
    return filtered_logs


@pytest.mark.e2e
def test_basic_lambda_logs_visible(deploy_lambdas, config):

    filtered_logs = fetch_logs(lambda_arn=deploy_lambdas["basichandlerarn"])

    assert any(log.message == config["MESSAGE"] and log.level == config["LOG_LEVEL"] for log in filtered_logs)


@pytest.mark.e2e
def test_basic_lambda_no_debug_logs_visible(deploy_lambdas, config):
    filtered_logs = fetch_logs(lambda_arn=deploy_lambdas["basichandlerarn"])

    assert not any(log.message == config["MESSAGE"] and log.level == "DEBUG" for log in filtered_logs)


@pytest.mark.e2e
def test_basic_lambda_contextual_data_logged(deploy_lambdas):
    filtered_logs = fetch_logs(lambda_arn=deploy_lambdas["basichandlerarn"])
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
def test_basic_lambda_additional_key_persistence_basic_lambda(deploy_lambdas, config):
    filtered_logs = fetch_logs(lambda_arn=deploy_lambdas["basichandlerarn"])

    assert any(
        log.extra_info and log.message == config["MESSAGE"] and log.level == config["LOG_LEVEL"]
        for log in filtered_logs
    )


@pytest.mark.e2e
def test_basic_lambda_empty_event_logged(deploy_lambdas):
    filtered_logs = fetch_logs(lambda_arn=deploy_lambdas["basichandlerarn"])

    assert any(log.message == {} for log in filtered_logs)


@pytest.mark.e2e
def test_no_context_lambda_contextual_data_not_logged(deploy_lambdas):
    filtered_logs = fetch_logs(lambda_arn=deploy_lambdas["nocontexthandlerarn"])

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
def test_no_context_lambda_event_not_logged(deploy_lambdas):
    filtered_logs = fetch_logs(lambda_arn=deploy_lambdas["nocontexthandlerarn"])

    assert not any(log.message == {} for log in filtered_logs)


### Add tests for cold start and non-cold start executions
### Test errors
### Test child loggers
