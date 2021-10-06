import datetime
import hashlib
import json
from collections import namedtuple
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable
from unittest import mock

import jmespath
import pytest
from botocore import stub
from botocore.config import Config
from jmespath import functions

from aws_lambda_powertools.shared.json_encoder import Encoder
from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer
from aws_lambda_powertools.utilities.idempotency.idempotency import IdempotencyConfig
from aws_lambda_powertools.utilities.jmespath_utils import extract_data_from_envelope
from aws_lambda_powertools.utilities.validation import envelopes
from tests.functional.utils import load_event

TABLE_NAME = "TEST_TABLE"


def serialize(data):
    return json.dumps(data, sort_keys=True, cls=Encoder)


@pytest.fixture(scope="module")
def config() -> Config:
    return Config(region_name="us-east-1")


@pytest.fixture(scope="module")
def lambda_apigw_event():
    return load_event("apiGatewayProxyV2Event.json")


@pytest.fixture
def lambda_context():
    lambda_context = {
        "function_name": "test-func",
        "memory_limit_in_mb": 128,
        "invoked_function_arn": "arn:aws:lambda:eu-west-1:809313241234:function:test-func",
        "aws_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
    }

    return namedtuple("LambdaContext", lambda_context.keys())(*lambda_context.values())


@pytest.fixture
def timestamp_future():
    return str(int((datetime.datetime.now() + datetime.timedelta(seconds=3600)).timestamp()))


@pytest.fixture
def timestamp_expired():
    now = datetime.datetime.now()
    period = datetime.timedelta(seconds=6400)
    return str(int((now - period).timestamp()))


@pytest.fixture(scope="module")
def lambda_response():
    return {"message": "test", "statusCode": 200, "decimal_val": Decimal("2.5"), "decimal_NaN": Decimal("NaN")}


@pytest.fixture(scope="module")
def serialized_lambda_response(lambda_response):
    return serialize(lambda_response)


@pytest.fixture(scope="module")
def deserialized_lambda_response(lambda_response):
    return json.loads(serialize(lambda_response))


@pytest.fixture
def default_jmespath():
    return "[body, queryStringParameters]"


@pytest.fixture
def expected_params_update_item(serialized_lambda_response):
    return lambda key: {
        "ExpressionAttributeNames": {"#expiry": "expiration", "#response_data": "data", "#status": "status"},
        "ExpressionAttributeValues": {
            ":expiry": stub.ANY,
            ":response_data": serialized_lambda_response,
            ":status": "COMPLETED",
        },
        "Key": key,
        "TableName": "TEST_TABLE",
        "UpdateExpression": "SET #response_data = :response_data, " "#expiry = :expiry, #status = :status",
    }


@pytest.fixture
def expected_params_update_item_with_validation(serialized_lambda_response, hashed_validation_key):
    return lambda key: {
        "ExpressionAttributeNames": {
            "#expiry": "expiration",
            "#response_data": "data",
            "#status": "status",
            "#validation_key": "validation",
        },
        "ExpressionAttributeValues": {
            ":expiry": stub.ANY,
            ":response_data": serialized_lambda_response,
            ":status": "COMPLETED",
            ":validation_key": hashed_validation_key,
        },
        "Key": key,
        "TableName": "TEST_TABLE",
        "UpdateExpression": "SET #response_data = :response_data, "
        "#expiry = :expiry, #status = :status, "
        "#validation_key = :validation_key",
    }


@pytest.fixture
def expected_params_put_item():
    return lambda key_attr, key: {
        "ConditionExpression": "attribute_not_exists(#id) OR #now < :now",
        "ExpressionAttributeNames": {"#id": key_attr, "#now": "expiration"},
        "ExpressionAttributeValues": {":now": stub.ANY},
        "Item": {"expiration": stub.ANY, "status": "INPROGRESS", **key},
        "TableName": "TEST_TABLE",
    }


@pytest.fixture
def expected_params_put_item_with_validation(hashed_validation_key):
    return lambda key_attr, key: {
        "ConditionExpression": "attribute_not_exists(#id) OR #now < :now",
        "ExpressionAttributeNames": {"#id": key_attr, "#now": "expiration"},
        "ExpressionAttributeValues": {":now": stub.ANY},
        "Item": {"expiration": stub.ANY, "status": "INPROGRESS", "validation": hashed_validation_key, **key},
        "TableName": "TEST_TABLE",
    }


@pytest.fixture
def hashed_idempotency_key(lambda_apigw_event, default_jmespath, lambda_context):
    compiled_jmespath = jmespath.compile(default_jmespath)
    data = compiled_jmespath.search(lambda_apigw_event)
    return "test-func#" + hashlib.md5(serialize(data).encode()).hexdigest()


@pytest.fixture
def hashed_idempotency_key_with_envelope(lambda_apigw_event):
    event = extract_data_from_envelope(
        data=lambda_apigw_event, envelope=envelopes.API_GATEWAY_HTTP, jmespath_options={}
    )
    return "test-func#" + hashlib.md5(serialize(event).encode()).hexdigest()


@pytest.fixture
def hashed_validation_key(lambda_apigw_event):
    return hashlib.md5(serialize(lambda_apigw_event["requestContext"]).encode()).hexdigest()


@dataclass(eq=True, frozen=True)
class TestPersistenceStore:
    persistence_layer: DynamoDBPersistenceLayer
    key_attr: str
    expected_key: Callable[[str], dict]
    expected_key_values: Callable[[str], dict]


@pytest.fixture(params=[{}, {"key_attr": "PK", "key_attr_value": "powertools#idempotency", "sort_key_attr": "SK"}])
def test_persistence_store(config, request) -> TestPersistenceStore:
    expected_key = (
        lambda idempotency_key: {"PK": "powertools#idempotency", "SK": idempotency_key}
        if request.param
        else {"id": idempotency_key}
    )
    expected_key_values = (
        lambda idempotency_key: {"PK": {"S": "powertools#idempotency"}, "SK": {"S": idempotency_key}}
        if request.param
        else {"id": {"S": idempotency_key}}
    )
    return TestPersistenceStore(
        persistence_layer=DynamoDBPersistenceLayer(table_name=TABLE_NAME, boto_config=config, **request.param),
        key_attr="PK" if request.param else "id",
        expected_key=expected_key,
        expected_key_values=expected_key_values,
    )


@pytest.fixture
def persistence_store_with_composite_key(config):
    return DynamoDBPersistenceLayer(
        table_name=TABLE_NAME,
        boto_config=config,
    )


@pytest.fixture
def idempotency_config(config, request, default_jmespath):
    return IdempotencyConfig(
        event_key_jmespath=request.param.get("event_key_jmespath") or default_jmespath,
        use_local_cache=request.param["use_local_cache"],
    )


@pytest.fixture
def config_without_jmespath(config, request):
    return IdempotencyConfig(use_local_cache=request.param["use_local_cache"])


@pytest.fixture
def config_with_validation(config, request, default_jmespath):
    return IdempotencyConfig(
        event_key_jmespath=default_jmespath,
        use_local_cache=request.param,
        payload_validation_jmespath="requestContext",
    )


@pytest.fixture
def config_with_jmespath_options(config, request):
    class CustomFunctions(functions.Functions):
        @functions.signature({"types": ["string"]})
        def _func_echo_decoder(self, value):
            return value

    return IdempotencyConfig(
        use_local_cache=False,
        event_key_jmespath=request.param,
        jmespath_options={"custom_functions": CustomFunctions()},
    )


@pytest.fixture
def mock_function():
    return mock.MagicMock()
