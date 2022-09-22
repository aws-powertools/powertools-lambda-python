import json
from time import sleep

import pytest

from tests.e2e.utils import data_fetcher


@pytest.fixture
def ttl_expiration_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("TtlExpirationHandler", "")


@pytest.fixture
def ttl_expiration_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("TtlExpirationHandlerArn", "")


@pytest.fixture
def idempotency_table_name(infrastructure: dict) -> str:
    return infrastructure.get("DynamoDBTable", "")


def test_ttl_expiration_idempotency(ttl_expiration_handler_fn_arn: str, ttl_expiration_handler_fn: str):
    # GIVEN
    payload = json.dumps({"message": "Lambda Powertools - TTL 20 secs"})

    # WHEN
    # first call
    first_call, _ = data_fetcher.get_lambda_response(lambda_arn=ttl_expiration_handler_fn_arn, payload=payload)
    first_call_response = first_call["Payload"].read().decode("utf-8")

    # second call should return same response as first call
    second_call, _ = data_fetcher.get_lambda_response(lambda_arn=ttl_expiration_handler_fn_arn, payload=payload)
    second_call_response = second_call["Payload"].read().decode("utf-8")

    # wait 10s to expire ttl and call again, this should return a new value
    sleep(20)
    third_call, _ = data_fetcher.get_lambda_response(lambda_arn=ttl_expiration_handler_fn_arn, payload=payload)
    third_call_response = third_call["Payload"].read().decode("utf-8")

    # THEN
    assert first_call_response == second_call_response
    assert third_call_response != second_call_response
