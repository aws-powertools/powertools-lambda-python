import copy
import sys

import pytest
from botocore import stub

from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyAlreadyInProgressError,
    IdempotencyInconsistentStateError,
    IdempotencyPersistenceLayerError,
    IdempotencyValidationError,
)
from aws_lambda_powertools.utilities.idempotency.idempotency import idempotent

TABLE_NAME = "TEST_TABLE"


# Using parametrize to run test twice, with two separate instances of persistence store. One instance with caching
# enabled, and one without.
@pytest.mark.parametrize("persistence_store", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
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


@pytest.mark.parametrize("persistence_store", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
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

    with pytest.raises(IdempotencyAlreadyInProgressError) as ex:
        lambda_handler(lambda_apigw_event, {})
        assert (
            ex.value.args[0] == "Execution already in progress with idempotency key: "
            "body=a3edd699125517bb49d562501179ecbd"
        )

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="issue with pytest mock lib for < 3.8")
@pytest.mark.parametrize("persistence_store", [{"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_in_progress_with_cache(
    persistence_store, lambda_apigw_event, lambda_response, timestamp_future, hashed_idempotency_key, mocker
):
    """
    Test idempotent decorator where lambda_handler is already processing an event with matching event key, cache
    enabled.
    """
    save_to_cache_spy = mocker.spy(persistence_store, "_save_to_cache")
    retrieve_from_cache_spy = mocker.spy(persistence_store, "_retrieve_from_cache")
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

    loops = 3
    for _ in range(loops):
        with pytest.raises(IdempotencyAlreadyInProgressError) as ex:
            lambda_handler(lambda_apigw_event, {})
            assert (
                ex.value.args[0] == "Execution already in progress with idempotency key: "
                "body=a3edd699125517bb49d562501179ecbd"
            )

    assert retrieve_from_cache_spy.call_count == 2 * loops
    retrieve_from_cache_spy.assert_called_with(idempotency_key=hashed_idempotency_key)

    assert save_to_cache_spy.call_count == 1
    first_call_args_data_record = save_to_cache_spy.call_args_list[0].kwargs["data_record"]
    assert first_call_args_data_record.idempotency_key == hashed_idempotency_key
    assert first_call_args_data_record.status == "INPROGRESS"
    assert persistence_store._cache.get(hashed_idempotency_key)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("persistence_store", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_first_execution(
    persistence_store,
    lambda_apigw_event,
    expected_params_update_item,
    expected_params_put_item,
    lambda_response,
    hashed_idempotency_key,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)
    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="issue with pytest mock lib for < 3.8")
@pytest.mark.parametrize("persistence_store", [{"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_first_execution_cached(
    persistence_store,
    lambda_apigw_event,
    expected_params_update_item,
    expected_params_put_item,
    lambda_response,
    hashed_idempotency_key,
    mocker,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key. Ensure
    result is cached locally on the persistence store instance.
    """
    save_to_cache_spy = mocker.spy(persistence_store, "_save_to_cache")
    retrieve_from_cache_spy = mocker.spy(persistence_store, "_retrieve_from_cache")
    stubber = stub.Stubber(persistence_store.table.meta.client)
    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, {})

    assert retrieve_from_cache_spy.call_count == 1
    assert save_to_cache_spy.call_count == 2
    first_call_args, second_call_args = save_to_cache_spy.call_args_list
    assert first_call_args.args[0].status == "INPROGRESS"
    assert second_call_args.args[0].status == "COMPLETED"
    assert persistence_store._cache.get(hashed_idempotency_key)

    # This lambda call should not call AWS API
    lambda_handler(lambda_apigw_event, {})
    assert retrieve_from_cache_spy.call_count == 3
    retrieve_from_cache_spy.assert_called_with(idempotency_key=hashed_idempotency_key)

    # This assertion fails if an AWS API operation was called more than once
    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("persistence_store", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_expired(
    persistence_store,
    lambda_apigw_event,
    timestamp_expired,
    lambda_response,
    expected_params_update_item,
    expected_params_put_item,
    hashed_idempotency_key,
):
    """
    Test idempotent decorator when lambda is called with an event it succesfully handled already, but outside of the
    expiry window
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)

    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("persistence_store", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_exception(
    persistence_store,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    expected_params_put_item,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception which is retryable.
    """

    # Create a new provider

    # Stub the boto3 client
    stubber = stub.Stubber(persistence_store.table.meta.client)

    ddb_response = {}
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


@pytest.mark.parametrize(
    "persistence_store_with_validation", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True
)
def test_idempotent_lambda_already_completed_with_validation_bad_payload(
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

    with pytest.raises(IdempotencyValidationError):
        lambda_apigw_event["requestContext"]["accountId"] += "1"  # Alter the request payload
        lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("persistence_store", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
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
    ddb_response_get_item_missing = {}
    expected_params_get_item = {
        "TableName": TABLE_NAME,
        "Key": {"id": hashed_idempotency_key},
        "ConsistentRead": True,
    }

    # Simulate record repeatedly changing state between put_item and get_item
    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response_get_item, expected_params_get_item)

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response_get_item_missing)

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


@pytest.mark.parametrize("persistence_store", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_persistence_exception_updating(
    persistence_store,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    expected_params_put_item,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception which is retryable.
    """
    stubber = stub.Stubber(persistence_store.table.meta.client)

    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_client_error("delete_item", "UnrecoverableError")
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception("Something went wrong!")

    with pytest.raises(IdempotencyPersistenceLayerError):
        lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("persistence_store", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_persistence_exception_deleting(
    persistence_store,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    expected_params_put_item,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception which is retryable.
    """
    stubber = stub.Stubber(persistence_store.table.meta.client)

    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_client_error("update_item", "UnrecoverableError")
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        return {"message": "success!"}

    with pytest.raises(IdempotencyPersistenceLayerError):
        lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize(
    "persistence_store_with_validation", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True
)
def test_idempotent_lambda_first_execution_with_validation(
    persistence_store_with_validation,
    lambda_apigw_event,
    expected_params_update_item_with_validation,
    expected_params_put_item_with_validation,
    lambda_response,
    hashed_idempotency_key,
    hashed_validation_key,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key
    """
    stubber = stub.Stubber(persistence_store_with_validation.table.meta.client)
    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item_with_validation)
    stubber.add_response("update_item", ddb_response, expected_params_update_item_with_validation)
    stubber.activate()

    @idempotent(persistence_store=persistence_store_with_validation)
    def lambda_handler(lambda_apigw_event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, {})

    stubber.assert_no_pending_responses()
    stubber.deactivate()
