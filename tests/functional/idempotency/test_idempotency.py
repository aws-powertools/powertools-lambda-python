import copy
import json
import sys
from hashlib import md5

import jmespath
import pytest
from botocore import stub

from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyAlreadyInProgressError,
    IdempotencyInconsistentStateError,
    IdempotencyInvalidStatusError,
    IdempotencyKeyError,
    IdempotencyPersistenceLayerError,
    IdempotencyValidationError,
)
from aws_lambda_powertools.utilities.idempotency.idempotency import idempotent
from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer, DataRecord
from aws_lambda_powertools.utilities.validation import envelopes, validator

TABLE_NAME = "TEST_TABLE"


# Using parametrize to run test twice, with two separate instances of persistence store. One instance with caching
# enabled, and one without.
@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_already_completed(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    hashed_idempotency_key,
    serialized_lambda_response,
    deserialized_lambda_response,
    lambda_context,
):
    """
    Test idempotent decorator where event with matching event key has already been succesfully processed
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": serialized_lambda_response},
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

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception

    lambda_resp = lambda_handler(lambda_apigw_event, lambda_context)
    assert lambda_resp == deserialized_lambda_response

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_in_progress(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    lambda_response,
    timestamp_future,
    hashed_idempotency_key,
    lambda_context,
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
            "status": {"S": "INPROGRESS"},
        }
    }

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response, expected_params)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    with pytest.raises(IdempotencyAlreadyInProgressError) as ex:
        lambda_handler(lambda_apigw_event, lambda_context)
        assert (
            ex.value.args[0] == "Execution already in progress with idempotency key: "
            "body=a3edd699125517bb49d562501179ecbd"
        )

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="issue with pytest mock lib for < 3.8")
@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_in_progress_with_cache(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    lambda_response,
    timestamp_future,
    hashed_idempotency_key,
    mocker,
    lambda_context,
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
            "status": {"S": "INPROGRESS"},
        }
    }

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response, expected_params)

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", copy.deepcopy(ddb_response), copy.deepcopy(expected_params))

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", copy.deepcopy(ddb_response), copy.deepcopy(expected_params))
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    loops = 3
    for _ in range(loops):
        with pytest.raises(IdempotencyAlreadyInProgressError) as ex:
            lambda_handler(lambda_apigw_event, lambda_context)
            assert (
                ex.value.args[0] == "Execution already in progress with idempotency key: "
                "body=a3edd699125517bb49d562501179ecbd"
            )

    assert retrieve_from_cache_spy.call_count == 2 * loops
    retrieve_from_cache_spy.assert_called_with(idempotency_key=hashed_idempotency_key)

    save_to_cache_spy.assert_called()
    assert persistence_store._cache.get(hashed_idempotency_key) is None

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_first_execution(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    expected_params_update_item,
    expected_params_put_item,
    lambda_response,
    serialized_lambda_response,
    deserialized_lambda_response,
    hashed_idempotency_key,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)
    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item)
    stubber.add_response("update_item", ddb_response, expected_params_update_item)
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="issue with pytest mock lib for < 3.8")
@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_first_execution_cached(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event: DynamoDBPersistenceLayer,
    expected_params_update_item,
    expected_params_put_item,
    lambda_response,
    hashed_idempotency_key,
    mocker,
    lambda_context,
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

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, lambda_context)

    retrieve_from_cache_spy.assert_called_once()
    save_to_cache_spy.assert_called_once()
    assert save_to_cache_spy.call_args[0][0].status == "COMPLETED"
    assert persistence_store._cache.get(hashed_idempotency_key).status == "COMPLETED"

    # This lambda call should not call AWS API
    lambda_handler(lambda_apigw_event, lambda_context)
    assert retrieve_from_cache_spy.call_count == 3
    retrieve_from_cache_spy.assert_called_with(idempotency_key=hashed_idempotency_key)

    # This assertion fails if an AWS API operation was called more than once
    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_expired(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_expired,
    lambda_response,
    expected_params_update_item,
    expected_params_put_item,
    hashed_idempotency_key,
    lambda_context,
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

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_exception(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    expected_params_put_item,
    lambda_context,
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

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception("Something went wrong!")

    with pytest.raises(Exception):
        lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize(
    "config_with_validation", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True
)
def test_idempotent_lambda_already_completed_with_validation_bad_payload(
    config_with_validation: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    hashed_validation_key,
    lambda_context,
):
    """
    Test idempotent decorator where event with matching event key has already been successfully processed
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)
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

    @idempotent(config=config_with_validation, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    with pytest.raises(IdempotencyValidationError):
        lambda_apigw_event["requestContext"]["accountId"] += "1"  # Alter the request payload
        lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_expired_during_request(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_expired,
    lambda_response,
    expected_params_update_item,
    hashed_idempotency_key,
    lambda_context,
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

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    # max retries exceeded before get_item and put_item agree on item state, so exception gets raised
    with pytest.raises(IdempotencyInconsistentStateError):
        lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_persistence_exception_deleting(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    expected_params_put_item,
    lambda_context,
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

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        raise Exception("Something went wrong!")

    with pytest.raises(IdempotencyPersistenceLayerError) as exc:
        lambda_handler(lambda_apigw_event, lambda_context)

    assert exc.value.args[0] == "Failed to delete record from idempotency store"
    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_persistence_exception_updating(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    expected_params_put_item,
    lambda_context,
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

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return {"message": "success!"}

    with pytest.raises(IdempotencyPersistenceLayerError) as exc:
        lambda_handler(lambda_apigw_event, lambda_context)

    assert exc.value.args[0] == "Failed to update record state to success in idempotency store"
    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True)
def test_idempotent_persistence_exception_getting(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    lambda_response,
    hashed_idempotency_key,
    expected_params_put_item,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key, but
    lambda_handler raises an exception which is retryable.
    """
    stubber = stub.Stubber(persistence_store.table.meta.client)

    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_client_error("get_item", "UnexpectedException")
    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return {"message": "success!"}

    with pytest.raises(IdempotencyPersistenceLayerError) as exc:
        lambda_handler(lambda_apigw_event, lambda_context)

    assert exc.value.args[0] == "Failed to get record from idempotency store"
    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize(
    "config_with_validation", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True
)
def test_idempotent_lambda_first_execution_with_validation(
    config_with_validation: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    expected_params_update_item_with_validation,
    expected_params_put_item_with_validation,
    lambda_response,
    hashed_idempotency_key,
    hashed_validation_key,
    lambda_context,
):
    """
    Test idempotent decorator when lambda is executed with an event with a previously unknown event key
    """
    stubber = stub.Stubber(persistence_store.table.meta.client)
    ddb_response = {}

    stubber.add_response("put_item", ddb_response, expected_params_put_item_with_validation)
    stubber.add_response("update_item", ddb_response, expected_params_update_item_with_validation)
    stubber.activate()

    @idempotent(config=config_with_validation, persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    lambda_handler(lambda_apigw_event, lambda_context)

    stubber.assert_no_pending_responses()
    stubber.deactivate()


@pytest.mark.parametrize(
    "config_without_jmespath", [{"use_local_cache": False}, {"use_local_cache": True}], indirect=True
)
def test_idempotent_lambda_with_validator_util(
    config_without_jmespath: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    serialized_lambda_response,
    deserialized_lambda_response,
    hashed_idempotency_key_with_envelope,
    mock_function,
    lambda_context,
):
    """
    Test idempotent decorator where event with matching event key has already been succesfully processed, using the
    validator utility to unwrap the event
    """

    stubber = stub.Stubber(persistence_store.table.meta.client)
    ddb_response = {
        "Item": {
            "id": {"S": hashed_idempotency_key_with_envelope},
            "expiration": {"N": timestamp_future},
            "data": {"S": serialized_lambda_response},
            "status": {"S": "COMPLETED"},
        }
    }

    expected_params = {
        "TableName": TABLE_NAME,
        "Key": {"id": hashed_idempotency_key_with_envelope},
        "ConsistentRead": True,
    }
    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    stubber.add_response("get_item", ddb_response, expected_params)
    stubber.activate()

    @validator(envelope=envelopes.API_GATEWAY_HTTP)
    @idempotent(config=config_without_jmespath, persistence_store=persistence_store)
    def lambda_handler(event, context):
        mock_function()
        return "shouldn't get here!"

    mock_function.assert_not_called()
    lambda_resp = lambda_handler(lambda_apigw_event, lambda_context)
    assert lambda_resp == deserialized_lambda_response

    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_data_record_invalid_status_value():
    data_record = DataRecord("key", status="UNSUPPORTED_STATUS")
    with pytest.raises(IdempotencyInvalidStatusError) as e:
        _ = data_record.status

    assert e.value.args[0] == "UNSUPPORTED_STATUS"


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_in_progress_never_saved_to_cache(
    idempotency_config: IdempotencyConfig, persistence_store: DynamoDBPersistenceLayer
):
    # GIVEN a data record with status "INPROGRESS"
    # and persistence_store has use_local_cache = True
    persistence_store.configure(idempotency_config)
    data_record = DataRecord("key", status="INPROGRESS")

    # WHEN saving to local cache
    persistence_store._save_to_cache(data_record)

    # THEN don't save to local cache
    assert persistence_store._cache.get("key") is None


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}], indirect=True)
def test_user_local_disabled(idempotency_config: IdempotencyConfig, persistence_store: DynamoDBPersistenceLayer):
    # GIVEN a persistence_store with use_local_cache = False
    persistence_store.configure(idempotency_config)

    # WHEN calling any local cache options
    data_record = DataRecord("key", status="COMPLETED")
    try:
        persistence_store._save_to_cache(data_record)
        cache_value = persistence_store._retrieve_from_cache("key")
        assert cache_value is None
        persistence_store._delete_from_cache("key")
    except AttributeError as e:
        pytest.fail(f"AttributeError should not be raised: {e}")

    # THEN raise AttributeError
    # AND don't have a _cache attribute
    assert not hasattr("persistence_store", "_cache")


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_delete_from_cache_when_empty(
    idempotency_config: IdempotencyConfig, persistence_store: DynamoDBPersistenceLayer
):
    # GIVEN use_local_cache is True AND the local cache is empty
    persistence_store.configure(idempotency_config)

    try:
        # WHEN we _delete_from_cache
        persistence_store._delete_from_cache("key_does_not_exist")
    except KeyError:
        # THEN we should not get a KeyError
        pytest.fail("KeyError should not happen")


def test_is_missing_idempotency_key():
    # GIVEN an empty tuple THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key(())
    # GIVEN an empty list THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key([])
    # GIVEN an empty dictionary THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key({})
    # GIVEN an empty str THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key("")
    # GIVEN False THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key(False)
    # GIVEN number 0 THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key(0)

    # GIVEN None THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key(None)
    # GIVEN a list of Nones THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key([None, None])
    # GIVEN a tuples of Nones THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key((None, None))
    # GIVEN a dict of Nones THEN is_missing_idempotency_key is True
    assert BasePersistenceLayer.is_missing_idempotency_key({None: None})

    # GIVEN a str THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key("Value") is False
    # GIVEN str "False" THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key("False") is False
    # GIVEN an number THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key(1000) is False
    # GIVEN a float THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key(10.01) is False
    # GIVEN a list of all not None THEN is_missing_idempotency_key is False
    assert BasePersistenceLayer.is_missing_idempotency_key([None, "Value"]) is False


@pytest.mark.parametrize(
    "idempotency_config", [{"use_local_cache": False, "event_key_jmespath": "body"}], indirect=True
)
def test_default_no_raise_on_missing_idempotency_key(
    idempotency_config: IdempotencyConfig, persistence_store: DynamoDBPersistenceLayer, lambda_context
):
    # GIVEN a persistence_store with use_local_cache = False and event_key_jmespath = "body"
    persistence_store.configure(idempotency_config)
    assert persistence_store.use_local_cache is False
    assert "body" in persistence_store.event_key_jmespath

    # WHEN getting the hashed idempotency key for an event with no `body` key
    hashed_key = persistence_store._get_hashed_idempotency_key({}, lambda_context)

    # THEN return the hash of None
    expected_value = "test-func#" + md5(json.dumps(None).encode()).hexdigest()
    assert expected_value == hashed_key


@pytest.mark.parametrize(
    "idempotency_config", [{"use_local_cache": False, "event_key_jmespath": "[body, x]"}], indirect=True
)
def test_raise_on_no_idempotency_key(
    idempotency_config: IdempotencyConfig, persistence_store: DynamoDBPersistenceLayer, lambda_context
):
    # GIVEN a persistence_store with raise_on_no_idempotency_key and no idempotency key in the request
    persistence_store.configure(idempotency_config)
    persistence_store.raise_on_no_idempotency_key = True
    assert persistence_store.use_local_cache is False
    assert "body" in persistence_store.event_key_jmespath

    # WHEN getting the hashed idempotency key for an event with no `body` key
    with pytest.raises(IdempotencyKeyError) as excinfo:
        persistence_store._get_hashed_idempotency_key({}, lambda_context)

    # THEN raise IdempotencyKeyError error
    assert "No data found to create a hashed idempotency_key" in str(excinfo.value)


@pytest.mark.parametrize(
    "idempotency_config",
    [
        {
            "use_local_cache": False,
            "event_key_jmespath": "[requestContext.authorizer.claims.sub, powertools_json(body).id]",
        }
    ],
    indirect=True,
)
def test_jmespath_with_powertools_json(
    idempotency_config: IdempotencyConfig, persistence_store: DynamoDBPersistenceLayer, lambda_context
):
    # GIVEN an event_key_jmespath with powertools_json custom function
    persistence_store.configure(idempotency_config)
    sub_attr_value = "cognito_user"
    key_attr_value = "some_key"
    expected_value = [sub_attr_value, key_attr_value]
    api_gateway_proxy_event = {
        "requestContext": {"authorizer": {"claims": {"sub": sub_attr_value}}},
        "body": json.dumps({"id": key_attr_value}),
    }

    # WHEN calling _get_hashed_idempotency_key
    result = persistence_store._get_hashed_idempotency_key(api_gateway_proxy_event, lambda_context)

    # THEN the hashed idempotency key should match the extracted values generated hash
    assert result == "test-func#" + persistence_store._generate_hash(expected_value)


@pytest.mark.parametrize("config_with_jmespath_options", ["powertools_json(data).payload"], indirect=True)
def test_custom_jmespath_function_overrides_builtin_functions(
    config_with_jmespath_options: IdempotencyConfig, persistence_store: DynamoDBPersistenceLayer, lambda_context
):
    # GIVEN an persistence store with a custom jmespath_options
    # AND use a builtin powertools custom function
    persistence_store.configure(config_with_jmespath_options)

    with pytest.raises(jmespath.exceptions.UnknownFunctionError, match="Unknown function: powertools_json()"):
        # WHEN calling _get_hashed_idempotency_key
        # THEN raise unknown function
        persistence_store._get_hashed_idempotency_key({}, lambda_context)


def test_idempotent_lambda_save_inprogress_error(persistence_store: DynamoDBPersistenceLayer, lambda_context):
    # GIVEN a miss configured persistence layer
    # like no table was created for the idempotency persistence layer
    stubber = stub.Stubber(persistence_store.table.meta.client)
    stubber.add_client_error("put_item", "ResourceNotFoundException")
    stubber.activate()

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        return {}

    # WHEN handling the idempotent call
    # AND save_inprogress raises a ClientError
    with pytest.raises(IdempotencyPersistenceLayerError) as e:
        lambda_handler({}, lambda_context)

    # THEN idempotent should raise an IdempotencyPersistenceLayerError
    stubber.assert_no_pending_responses()
    stubber.deactivate()
    assert "Failed to save in progress record to idempotency store" == e.value.args[0]
