import base64
import datetime
import json
import os
import pickle

import pytest
from botocore import stub
from botocore.config import Config

from aws_lambda_powertools.utilities.idempotency.exceptions import AlreadyInProgressError
from aws_lambda_powertools.utilities.idempotency.idempotency import idempotent
from aws_lambda_powertools.utilities.idempotency.persistence import DynamoDBPersistenceLayer


class CustomException1(Exception):
    pass


class CustomException2(Exception):
    pass


TABLE_NAME = "TEST_TABLE"


@pytest.fixture
def b64encoded_picked_error():
    return base64.b64encode(pickle.dumps(CustomException1("Somthing went wrong!"))).decode()


@pytest.fixture(scope="module")
def config() -> Config:
    return Config(region_name="us-east-1")


@pytest.fixture(scope="module")
def lambda_apigw_event():
    full_file_name = os.path.dirname(os.path.realpath(__file__)) + "/../events/" + "apiGatewayProxyV2Event.json"
    with open(full_file_name) as fp:
        event = json.load(fp)

    return event


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
    return {"message": "test", "statusCode": 200}


@pytest.fixture
def expected_params_update_item(lambda_response, md5hashed_idempotency_key):
    return {
        "ExpressionAttributeNames": {"#expiry": "expiration", "#response_data": "data", "#status": "status"},
        "ExpressionAttributeValues": {
            ":expiry": stub.ANY,
            ":response_data": json.dumps(lambda_response),
            ":status": "COMPLETED",
        },
        "Key": {"id": md5hashed_idempotency_key},
        "TableName": "TEST_TABLE",
        "UpdateExpression": "SET #response_data = :response_data, " "#expiry = :expiry, #status = :status",
    }


@pytest.fixture(scope="session")
def md5hashed_idempotency_key():
    return "e730b8578240b31b9a999c7fabf5f9bb"


@pytest.fixture
def persistence_store(config):
    persistence_store = DynamoDBPersistenceLayer(event_key="body", table_name=TABLE_NAME, boto_config=config)
    return persistence_store


def test_idempotent_lambda_already_completed(
    persistence_store, lambda_apigw_event, timestamp_future, lambda_response, md5hashed_idempotency_key,
):
    """
    Test idempotent decorator where event with matching event key has already been succesfully processed
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)
    ddb_response = {
        "Item": {
            "id": {"S": md5hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "COMPLETED"},
        }
    }

    expected_params = {
        "TableName": TABLE_NAME,
        "Key": {"id": md5hashed_idempotency_key},
        "ConsistentRead": True,
    }
    stubber.add_response("get_item", ddb_response, expected_params)
    stubber.activate()

    @idempotent(persistence=persistence_store)
    def lambda_handler(event, context):
        raise Exception

    lambda_resp = lambda_handler(lambda_apigw_event, {})
    assert lambda_resp == lambda_response

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotent_lambda_in_progress(
    persistence_store, lambda_apigw_event, lambda_response, timestamp_future, md5hashed_idempotency_key
):
    """
    Test idempotent decorator where lambda_handler is already processing an event with matching event key
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)

    expected_params = {
        "TableName": TABLE_NAME,
        "Key": {"id": md5hashed_idempotency_key},
        "ConsistentRead": True,
    }
    ddb_response = {
        "Item": {
            "id": {"S": md5hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "INPROGRESS"},
        }
    }

    stubber.add_response("get_item", ddb_response, expected_params)
    stubber.activate()

    @idempotent(persistence=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    with pytest.raises(AlreadyInProgressError) as ex:
        lambda_handler(lambda_apigw_event, {})
        assert (
            ex.value.args[0] == "Execution already in progress with idempotency key: "
            "body=a3edd699125517bb49d562501179ecbd"
        )
        print(ex)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotent_lambda_first_execution(
    persistence_store, lambda_apigw_event, expected_params_update_item, lambda_response, md5hashed_idempotency_key
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)
    ddb_response = {}

    expected_params_get_item = {
        "TableName": TABLE_NAME,
        "Key": {"id": md5hashed_idempotency_key},
        "ConsistentRead": True,
    }
    expected_params_put_item = {
        "ConditionExpression": "attribute_not_exists(id) OR expiration < :now",
        "ExpressionAttributeValues": {":now": stub.ANY},
        "Item": {"expiration": stub.ANY, "id": md5hashed_idempotency_key, "status": "INPROGRESS"},
        "TableName": "TEST_TABLE",
    }

    stubber.add_response("get_item", ddb_response, expected_params_get_item)
    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(persistence=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotent_lambda_expired(
    persistence_store,
    lambda_apigw_event,
    timestamp_expired,
    lambda_response,
    expected_params_update_item,
    md5hashed_idempotency_key,
):
    """
    Test idempotent decorator when lambda is called with an event it succesfully handled already, but outside of the
    expiry window
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)

    ddb_response = {}
    ddb_response_get_item = {
        "Item": {
            "id": {"S": md5hashed_idempotency_key},
            "expiration": {"N": timestamp_expired},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "INPROGRESS"},
        }
    }
    expected_params_get_item = {
        "TableName": TABLE_NAME,
        "Key": {"id": md5hashed_idempotency_key},
        "ConsistentRead": True,
    }

    stubber.add_response("get_item", ddb_response_get_item, expected_params_get_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(persistence=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


# Note - this test will need to change depending on how we define event handling behavior
def test_idempotent_lambda_exception_retryable_error(
    persistence_store, lambda_apigw_event, timestamp_future, lambda_response, md5hashed_idempotency_key
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception which is retryable.
    """

    # Create a new provider

    # Stub the boto3 client
    stubber = stub.Stubber(persistence_store.table.meta.client)

    ddb_response = {}
    ddb_response_get_item = {}
    expected_params_get_item = {
        "TableName": TABLE_NAME,
        "Key": {"id": md5hashed_idempotency_key},
        "ConsistentRead": True,
    }
    expected_params_put_item = {
        "ConditionExpression": "attribute_not_exists(id) OR expiration < :now",
        "ExpressionAttributeValues": {":now": stub.ANY},
        "Item": {"expiration": stub.ANY, "id": md5hashed_idempotency_key, "status": "INPROGRESS"},
        "TableName": "TEST_TABLE",
    }
    expected_params_delete_item = {"TableName": TABLE_NAME, "Key": {"id": md5hashed_idempotency_key}}

    stubber.add_response("get_item", ddb_response_get_item, expected_params_get_item)
    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("delete_item", ddb_response, expected_params_delete_item)
    stubber.activate()

    @idempotent(persistence=persistence_store)
    def lambda_handler(event, context):
        raise Exception("Something went wrong!")

    with pytest.raises(Exception):
        lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotent_lambda_exception_non_retryable_error(
    config, lambda_apigw_event, timestamp_future, lambda_response, b64encoded_picked_error, md5hashed_idempotency_key
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception.
    """

    persistence_store = DynamoDBPersistenceLayer(
        event_key="body", table_name=TABLE_NAME, non_retryable_errors=(CustomException1,), boto_config=config
    )

    stubber = stub.Stubber(persistence_store.table.meta.client)

    ddb_response_get_item = {
        "Item": {
            "id": {"S": md5hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": b64encoded_picked_error},
            "status": {"S": "ERROR"},
        }
    }
    expected_params_get_item = {
        "TableName": TABLE_NAME,
        "Key": {"id": md5hashed_idempotency_key},
        "ConsistentRead": True,
    }

    stubber.add_response("get_item", ddb_response_get_item, expected_params_get_item)
    stubber.activate()

    @idempotent(persistence=persistence_store)
    def lambda_handler(event, context):
        raise CustomException1("Somthing went wrong!")

    with pytest.raises(CustomException1):
        lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_create_table():
    pass
