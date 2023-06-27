import json
from time import sleep

import pytest

from tests.e2e.utils import data_fetcher
from tests.e2e.utils.functions import execute_lambdas_in_parallel


@pytest.fixture
def ttl_cache_expiration_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("TtlCacheExpirationHandlerArn", "")


@pytest.fixture
def ttl_cache_timeout_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("TtlCacheTimeoutHandlerArn", "")


@pytest.fixture
def parallel_execution_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("ParallelExecutionHandlerArn", "")


@pytest.fixture
def function_thread_safety_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("FunctionThreadSafetyHandlerArn", "")


@pytest.fixture
def optional_idempotency_key_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("OptionalIdempotencyKeyHandlerArn", "")


@pytest.fixture
def idempotency_table_name(infrastructure: dict) -> str:
    return infrastructure.get("DynamoDBTable", "")


@pytest.mark.xdist_group(name="idempotency")
def test_ttl_caching_expiration_idempotency(ttl_cache_expiration_handler_fn_arn: str):
    # GIVEN
    payload = json.dumps({"message": "Powertools for AWS Lambda (Python) - TTL 5s"})

    # WHEN
    # first execution
    first_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=ttl_cache_expiration_handler_fn_arn,
        payload=payload,
    )
    first_execution_response = first_execution["Payload"].read().decode("utf-8")

    # the second execution should return the same response as the first execution
    second_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=ttl_cache_expiration_handler_fn_arn,
        payload=payload,
    )
    second_execution_response = second_execution["Payload"].read().decode("utf-8")

    # wait 8s to expire ttl and execute again, this should return a new response value
    sleep(8)
    third_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=ttl_cache_expiration_handler_fn_arn,
        payload=payload,
    )
    third_execution_response = third_execution["Payload"].read().decode("utf-8")

    # THEN
    assert first_execution_response == second_execution_response
    assert third_execution_response != second_execution_response


@pytest.mark.xdist_group(name="idempotency")
def test_ttl_caching_timeout_idempotency(ttl_cache_timeout_handler_fn_arn: str):
    # GIVEN
    payload_timeout_execution = json.dumps({"sleep": 5, "message": "Powertools for AWS Lambda (Python) - TTL 1s"})
    payload_working_execution = json.dumps({"sleep": 0, "message": "Powertools for AWS Lambda (Python) - TTL 1s"})

    # WHEN
    # first call should fail due to timeout
    execution_with_timeout, _ = data_fetcher.get_lambda_response(
        lambda_arn=ttl_cache_timeout_handler_fn_arn,
        payload=payload_timeout_execution,
    )
    execution_with_timeout_response = execution_with_timeout["Payload"].read().decode("utf-8")

    # the second call should work and return the payload
    execution_working, _ = data_fetcher.get_lambda_response(
        lambda_arn=ttl_cache_timeout_handler_fn_arn,
        payload=payload_working_execution,
    )
    execution_working_response = execution_working["Payload"].read().decode("utf-8")

    # THEN
    assert "Task timed out after" in execution_with_timeout_response
    assert payload_working_execution == execution_working_response


@pytest.mark.xdist_group(name="idempotency")
def test_parallel_execution_idempotency(parallel_execution_handler_fn_arn: str):
    # GIVEN
    arguments = json.dumps({"message": "Powertools for AWS Lambda (Python) - Parallel execution"})

    # WHEN
    # executing Lambdas in parallel
    lambdas_arn = [parallel_execution_handler_fn_arn, parallel_execution_handler_fn_arn]
    execution_result_list = execute_lambdas_in_parallel("data_fetcher.get_lambda_response", lambdas_arn, arguments)

    timeout_execution_response = execution_result_list[0][0]["Payload"].read().decode("utf-8")
    error_idempotency_execution_response = execution_result_list[1][0]["Payload"].read().decode("utf-8")

    # THEN
    assert "Execution already in progress with idempotency key" in error_idempotency_execution_response
    assert "Task timed out after" in timeout_execution_response


@pytest.mark.xdist_group(name="idempotency")
def test_idempotent_function_thread_safety(function_thread_safety_handler_fn_arn: str):
    # GIVEN
    payload = json.dumps({"message": "Powertools for AWS Lambda (Python) - Idempotent function thread safety check"})

    # WHEN
    # first execution
    first_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=function_thread_safety_handler_fn_arn,
        payload=payload,
    )
    first_execution_response = first_execution["Payload"].read().decode("utf-8")

    # the second execution should return the same response as the first execution
    second_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=function_thread_safety_handler_fn_arn,
        payload=payload,
    )
    second_execution_response = second_execution["Payload"].read().decode("utf-8")

    # THEN
    # Function threads finished without exception AND
    # first and second execution is the same
    for function_thread in json.loads(first_execution_response):
        assert function_thread["state"] == "FINISHED"
        assert function_thread["exception"] is None
        assert function_thread["output"] is not None

    # we use set() here because we want to compare the elements regardless of their order in the array
    assert set(first_execution_response) == set(second_execution_response)


@pytest.mark.xdist_group(name="idempotency")
def test_optional_idempotency_key(optional_idempotency_key_fn_arn: str):
    # GIVEN two payloads where only one has the expected idempotency key
    payload = json.dumps({"headers": {"X-Idempotency-Key": "here"}})
    payload_without = json.dumps({"headers": {}})

    # WHEN
    # we make one request with an idempotency key
    first_execution, _ = data_fetcher.get_lambda_response(lambda_arn=optional_idempotency_key_fn_arn, payload=payload)
    first_execution_response = first_execution["Payload"].read().decode("utf-8")

    # and two others without the idempotency key
    second_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=optional_idempotency_key_fn_arn,
        payload=payload_without,
    )
    second_execution_response = second_execution["Payload"].read().decode("utf-8")

    third_execution, _ = data_fetcher.get_lambda_response(
        lambda_arn=optional_idempotency_key_fn_arn,
        payload=payload_without,
    )
    third_execution_response = third_execution["Payload"].read().decode("utf-8")

    # THEN
    # we should treat 2nd and 3rd requests with NULL idempotency key as non-idempotent transactions
    # that is, no cache, no calls to persistent store, etc.
    assert first_execution_response != second_execution_response
    assert first_execution_response != third_execution_response
    assert second_execution_response != third_execution_response
