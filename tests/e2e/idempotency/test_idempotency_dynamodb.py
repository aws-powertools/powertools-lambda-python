import json

import pytest

from tests.e2e.utils import data_fetcher


@pytest.fixture
def basic_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandler", "")


@pytest.fixture
def basic_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandlerArn", "")


@pytest.fixture
def idempotency_table_name(infrastructure: dict) -> str:
    return infrastructure.get("DynamoDBTable", "")


def test_basic_idempotency_record(basic_handler_fn_arn: str, basic_handler_fn: str, idempotency_table_name: str):
    # GIVEN
    function_name = "basic_handler.lambda_handler"
    table_name = idempotency_table_name
    payload = json.dumps({"message": "Lambda Powertools"})

    # WHEN
    data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=payload)

    # THEN
    ddb_records = data_fetcher.get_ddb_idempotency_record(function_name=function_name, table_name=table_name)

    assert ddb_records == 1
