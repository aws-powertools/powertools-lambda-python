import datetime
import json
from decimal import Decimal
from unittest import mock

import jmespath
import pytest
from botocore import stub
from botocore.config import Config
from jmespath import functions

from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer
from aws_lambda_powertools.utilities.idempotency.idempotency import IdempotencyConfig
from aws_lambda_powertools.utilities.jmespath_utils import extract_data_from_envelope
from aws_lambda_powertools.utilities.validation import envelopes
from tests.functional.idempotency.utils import hash_idempotency_key
from tests.functional.utils import json_serialize, load_event

TABLE_NAME = "TEST_TABLE"


@pytest.fixture(scope="module")
def config() -> Config:
    return Config(region_name="us-east-1")


@pytest.fixture(scope="module")
def lambda_apigw_event():
    return load_event("apiGatewayProxyV2Event.json")


@pytest.fixture
def lambda_context():
    class LambdaContext:
        def __init__(self):
            self.function_name = "test-func"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:eu-west-1:809313241234:function:test-func"
            self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"

        def get_remaining_time_in_millis(self) -> int:
            return 1000

    return LambdaContext()


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
    return json_serialize(lambda_response)


@pytest.fixture(scope="module")
def deserialized_lambda_response(lambda_response):
    return json.loads(json_serialize(lambda_response))


@pytest.fixture
def default_jmespath():
    return "[body, queryStringParameters]"


@pytest.fixture
def expected_params_update_item(serialized_lambda_response, hashed_idempotency_key):
    return {
        "ExpressionAttributeNames": {
            "#expiry": "expiration",
            "#response_data": "data",
            "#status": "status",
        },
        "ExpressionAttributeValues": {
            ":expiry": {"N": stub.ANY},
            ":response_data": {"S": serialized_lambda_response},
            ":status": {"S": "COMPLETED"},
        },
        "Key": {"id": {"S": hashed_idempotency_key}},
        "TableName": "TEST_TABLE",
        "UpdateExpression": "SET #response_data = :response_data, " "#expiry = :expiry, #status = :status",
    }


@pytest.fixture
def expected_params_update_item_with_validation(
    serialized_lambda_response, hashed_idempotency_key, hashed_validation_key
):
    return {
        "ExpressionAttributeNames": {
            "#expiry": "expiration",
            "#response_data": "data",
            "#status": "status",
            "#validation_key": "validation",
        },
        "ExpressionAttributeValues": {
            ":expiry": {"N": stub.ANY},
            ":response_data": {"S": serialized_lambda_response},
            ":status": {"S": "COMPLETED"},
            ":validation_key": {"S": hashed_validation_key},
        },
        "Key": {"id": {"S": hashed_idempotency_key}},
        "TableName": "TEST_TABLE",
        "UpdateExpression": (
            "SET #response_data = :response_data, "
            "#expiry = :expiry, #status = :status, "
            "#validation_key = :validation_key"
        ),
    }


@pytest.fixture
def expected_params_put_item(hashed_idempotency_key):
    return {
        "ConditionExpression": (
            "attribute_not_exists(#id) OR #expiry < :now OR "
            "(#status = :inprogress AND attribute_exists(#in_progress_expiry) AND #in_progress_expiry < :now_in_millis)"
        ),
        "ExpressionAttributeNames": {
            "#id": "id",
            "#expiry": "expiration",
            "#status": "status",
            "#in_progress_expiry": "in_progress_expiration",
        },
        "ExpressionAttributeValues": {
            ":now": {"N": stub.ANY},
            ":now_in_millis": {"N": stub.ANY},
            ":inprogress": {"S": "INPROGRESS"},
        },
        "Item": {
            "expiration": {"N": stub.ANY},
            "in_progress_expiration": {"N": stub.ANY},
            "id": {"S": hashed_idempotency_key},
            "status": {"S": "INPROGRESS"},
        },
        "TableName": "TEST_TABLE",
    }


@pytest.fixture
def expected_params_put_item_with_validation(hashed_idempotency_key, hashed_validation_key):
    return {
        "ConditionExpression": (
            "attribute_not_exists(#id) OR #expiry < :now OR "
            "(#status = :inprogress AND attribute_exists(#in_progress_expiry) AND #in_progress_expiry < :now_in_millis)"
        ),
        "ExpressionAttributeNames": {
            "#id": "id",
            "#expiry": "expiration",
            "#status": "status",
            "#in_progress_expiry": "in_progress_expiration",
        },
        "ExpressionAttributeValues": {
            ":now": {"N": stub.ANY},
            ":now_in_millis": {"N": stub.ANY},
            ":inprogress": {"S": "INPROGRESS"},
        },
        "Item": {
            "expiration": {"N": stub.ANY},
            "in_progress_expiration": {"N": stub.ANY},
            "id": {"S": hashed_idempotency_key},
            "status": {"S": "INPROGRESS"},
            "validation": {"S": hashed_validation_key},
        },
        "TableName": "TEST_TABLE",
    }


@pytest.fixture
def hashed_idempotency_key(request, lambda_apigw_event, default_jmespath, lambda_context):
    compiled_jmespath = jmespath.compile(default_jmespath)
    data = compiled_jmespath.search(lambda_apigw_event)
    return (
        f"test-func.{request.function.__module__}.{request.function.__qualname__}.<locals>.lambda_handler#"
        + hash_idempotency_key(data)
    )


@pytest.fixture
def hashed_idempotency_key_with_envelope(request, lambda_apigw_event):
    event = extract_data_from_envelope(
        data=lambda_apigw_event, envelope=envelopes.API_GATEWAY_HTTP, jmespath_options={}
    )
    return (
        f"test-func.{request.function.__module__}.{request.function.__qualname__}.<locals>.lambda_handler#"
        + hash_idempotency_key(event)
    )


@pytest.fixture
def hashed_validation_key(lambda_apigw_event):
    return hash_idempotency_key(lambda_apigw_event["requestContext"])


@pytest.fixture
def persistence_store(config):
    return DynamoDBPersistenceLayer(table_name=TABLE_NAME, boto_config=config)


@pytest.fixture
def persistence_store_compound(config):
    return DynamoDBPersistenceLayer(table_name=TABLE_NAME, boto_config=config, key_attr="id", sort_key_attr="sk")


@pytest.fixture
def persistence_store_compound_static_pk_value(config, static_pk_value):
    return DynamoDBPersistenceLayer(
        table_name=TABLE_NAME, boto_config=config, key_attr="id", sort_key_attr="sk", static_pk_value=static_pk_value
    )


@pytest.fixture
def idempotency_config(config, request, default_jmespath):
    return IdempotencyConfig(
        event_key_jmespath=request.param.get("event_key_jmespath") or default_jmespath,
        use_local_cache=request.param["use_local_cache"],
        payload_validation_jmespath=request.param.get("payload_validation_jmespath") or "",
    )


@pytest.fixture
def config_without_jmespath(config, request):
    return IdempotencyConfig(use_local_cache=request.param["use_local_cache"])


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


@pytest.fixture
def static_pk_value():
    return "static-value"


@pytest.fixture
def expected_params_update_item_compound_key_static_pk_value(
    expected_params_update_item, hashed_idempotency_key, static_pk_value
):
    return {
        # same as in any update_item transaction except the `Key` due to composite key value
        **expected_params_update_item,
        "Key": {"id": {"S": static_pk_value}, "sk": {"S": hashed_idempotency_key}},
    }


@pytest.fixture
def expected_params_put_item_compound_key_static_pk_value(
    expected_params_put_item, hashed_idempotency_key, static_pk_value
):
    return {
        # same as in any put_item transaction except the `Item` due to composite key value
        **expected_params_put_item,
        "Item": {
            "expiration": {"N": stub.ANY},
            "in_progress_expiration": {"N": stub.ANY},
            "id": {"S": static_pk_value},
            "sk": {"S": hashed_idempotency_key},
            "status": {"S": "INPROGRESS"},
        },
        "TableName": "TEST_TABLE",
    }
