import copy

import pytest
from botocore import stub

from aws_lambda_powertools.utilities.idempotency.exceptions import (
    AlreadyInProgressError,
    IdempotencyInconsistentStateError,
    IdempotencyValidationerror,
)
from aws_lambda_powertools.utilities.idempotency.idempotency import idempotent

TABLE_NAME = "TEST_TABLE"


def test_idempotent_lambda_already_completed(
    persistence_store, lambda_apigw_event, timestamp_future, lambda_response, hashed_idempotency_key,
):
    """
    Test idempotent decorator where event with matching event key has already been succesfully processed
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "COMPLETED"},
        }
    }

    expected_params = {
        "TableName": TABLE_NAME,
        "Key": {"id": hashed_idempotency_key},
        "ConsistentRead": True,
    }
    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response, expected_params)
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception

    lambda_resp = lambda_handler(lambda_apigw_event, {})
    assert lambda_resp == lambda_response

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotent_lambda_in_progress(
    persistence_store, lambda_apigw_event, lambda_response, timestamp_future, hashed_idempotency_key
):
    """
    Test idempotent decorator where lambda_handler is already processing an event with matching event key
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)

    expected_params = {
        "TableName": TABLE_NAME,
        "Key": {"id": hashed_idempotency_key},
        "ConsistentRead": True,
    }
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "INPROGRESS"},
        }
    }

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response, expected_params)
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
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
    persistence_store, lambda_apigw_event, expected_params_update_item, lambda_response, hashed_idempotency_key
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)
    ddb_response = {}

    expected_params_put_item = {
        "ConditionExpression": "attribute_not_exists(id) OR expiration < :now",
        "ExpressionAttributeValues": {":now": stub.ANY},
        "Item": {"expiration": stub.ANY, "id": hashed_idempotency_key, "status": "INPROGRESS"},
        "TableName": "TEST_TABLE",
    }
    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotent_lambda_first_execution_cached(
    persistence_store_with_cache,
    lambda_apigw_event,
    expected_params_update_item,
    lambda_response,
    hashed_idempotency_key,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key. Ensure
    result is cached locally on the persistence store instance.
    """

    stubber = stub.Stubber(persistence_store_with_cache.table.meta.client)
    ddb_response = {}

    expected_params_put_item = {
        "ConditionExpression": "attribute_not_exists(id) OR expiration < :now",
        "ExpressionAttributeValues": {":now": stub.ANY},
        "Item": {"expiration": stub.ANY, "id": hashed_idempotency_key, "status": "INPROGRESS"},
        "TableName": "TEST_TABLE",
    }

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(persistence_store=persistence_store_with_cache)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, {})

    assert persistence_store_with_cache._cache.get(hashed_idempotency_key)

    # This lambda call should not call AWS API
    lambda_handler(lambda_apigw_event, {})

    # This assertion fails if an AWS API operation was called more than once
    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotent_lambda_expired(
    persistence_store,
    lambda_apigw_event,
    timestamp_expired,
    lambda_response,
    expected_params_update_item,
    hashed_idempotency_key,
):
    """
    Test idempotent decorator when lambda is called with an event it succesfully handled already, but outside of the
    expiry window
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)

    ddb_response = {}
    ddb_response_get_item = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_expired},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "INPROGRESS"},
        }
    }
    expected_params_get_item = {
        "TableName": TABLE_NAME,
        "Key": {"id": hashed_idempotency_key},
        "ConsistentRead": True,
    }

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response_get_item, expected_params_get_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


# Note - this test will need to change depending on how we define event handling behavior
def test_idempotent_lambda_exception(
    persistence_store, lambda_apigw_event, timestamp_future, lambda_response, hashed_idempotency_key
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception which is retryable.
    """

    # Create a new provider

    # Stub the boto3 client
    stubber = stub.Stubber(persistence_store.table.meta.client)

    ddb_response = {}
    expected_params_put_item = {
        "ConditionExpression": "attribute_not_exists(id) OR expiration < :now",
        "ExpressionAttributeValues": {":now": stub.ANY},
        "Item": {"expiration": stub.ANY, "id": hashed_idempotency_key, "status": "INPROGRESS"},
        "TableName": "TEST_TABLE",
    }
    expected_params_delete_item = {"TableName": TABLE_NAME, "Key": {"id": hashed_idempotency_key}}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("delete_item", ddb_response, expected_params_delete_item)
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception("Something went wrong!")

    with pytest.raises(Exception):
        lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotent_lambda_already_completed_bad_payload(
    persistence_store_with_validation,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    hashed_validation_key,
):
    """
    Test idempotent decorator where event with matching event key has already been succesfully processed
    """

    stubber = stub.Stubber(persistence_store_with_validation.table.meta.client)
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "COMPLETED"},
            "validation": {"S": hashed_validation_key},
        }
    }

    expected_params = {"TableName": TABLE_NAME, "Key": {"id": hashed_idempotency_key}, "ConsistentRead": True}

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response, expected_params)
    stubber.activate()

    @idempotent(persistence_store=persistence_store_with_validation)
    def lambda_handler(event, context):
        return lambda_response

    with pytest.raises(IdempotencyValidationerror):
        lambda_apigw_event["requestContext"]["accountId"] += "1"  # Alter the request payload
        lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_idempotent_lambda_expired_during_request(
    persistence_store,
    lambda_apigw_event,
    timestamp_expired,
    lambda_response,
    expected_params_update_item,
    hashed_idempotency_key,
):
    """
    Test idempotent decorator when lambda is called with an event it succesfully handled already. Persistence store
    returns inconsistent/rapidly changing result between put_item and get_item calls.
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)

    ddb_response_get_item = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_expired},
            "data": {"S": '{"message": "test", "statusCode": 200}'},
            "status": {"S": "INPROGRESS"},
        }
    }
    expected_params_get_item = {
        "TableName": TABLE_NAME,
        "Key": {"id": hashed_idempotency_key},
        "ConsistentRead": True,
    }

    # Record repeatedly changes between put_item and get_item
    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response_get_item, expected_params_get_item)

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", copy.deepcopy(ddb_response_get_item), copy.deepcopy(expected_params_get_item))

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", copy.deepcopy(ddb_response_get_item), copy.deepcopy(expected_params_get_item))

    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    # max retries exceeded before get_item and put_item agree on item state, so exception gets raised
    with pytest.raises(IdempotencyInconsistentStateError):
        lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()
