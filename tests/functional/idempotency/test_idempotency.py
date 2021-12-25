import copy
import sys
from hashlib import md5
from unittest.mock import MagicMock

import jmespath
import pytest
from botocore import stub
from pydantic import BaseModel

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEventV2, event_source
from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig
from aws_lambda_powertools.utilities.idempotency.base import _prepare_data
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyAlreadyInProgressError,
    IdempotencyInconsistentStateError,
    IdempotencyInvalidStatusError,
    IdempotencyKeyError,
    IdempotencyPersistenceLayerError,
    IdempotencyValidationError,
)
from aws_lambda_powertools.utilities.idempotency.idempotency import idempotent, idempotent_function
from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer, DataRecord
from aws_lambda_powertools.utilities.validation import envelopes, validator
from tests.functional.utils import hash_idempotency_key, json_serialize, load_event

TABLE_NAME = "TEST_TABLE"


def get_dataclasses_lib():
    """Python 3.6 doesn't support dataclasses natively"""
    import dataclasses

    return dataclasses


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


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_idempotent_lambda_first_execution_cached(
    idempotency_config: IdempotencyConfig,
    persistence_store: DynamoDBPersistenceLayer,
    lambda_apigw_event,
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
    assert save_to_cache_spy.call_args[1]["data_record"].status == "COMPLETED"
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
    function_name = "foo"
    persistence_store.configure(idempotency_config, function_name)
    assert persistence_store.use_local_cache is False
    assert "body" in persistence_store.event_key_jmespath

    # WHEN getting the hashed idempotency key for an event with no `body` key
    hashed_key = persistence_store._get_hashed_idempotency_key({})

    # THEN return the hash of None
    expected_value = f"test-func.{function_name}#" + md5(json_serialize(None).encode()).hexdigest()
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
        persistence_store._get_hashed_idempotency_key({})

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
    persistence_store.configure(idempotency_config, "handler")
    sub_attr_value = "cognito_user"
    static_pk_value = "some_key"
    expected_value = [sub_attr_value, static_pk_value]
    api_gateway_proxy_event = {
        "requestContext": {"authorizer": {"claims": {"sub": sub_attr_value}}},
        "body": json_serialize({"id": static_pk_value}),
    }

    # WHEN calling _get_hashed_idempotency_key
    result = persistence_store._get_hashed_idempotency_key(api_gateway_proxy_event)

    # THEN the hashed idempotency key should match the extracted values generated hash
    assert result == "test-func.handler#" + persistence_store._generate_hash(expected_value)


@pytest.mark.parametrize("config_with_jmespath_options", ["powertools_json(data).payload"], indirect=True)
def test_custom_jmespath_function_overrides_builtin_functions(
    config_with_jmespath_options: IdempotencyConfig, persistence_store: DynamoDBPersistenceLayer, lambda_context
):
    # GIVEN a persistence store with a custom jmespath_options
    # AND use a builtin powertools custom function
    persistence_store.configure(config_with_jmespath_options)

    with pytest.raises(jmespath.exceptions.UnknownFunctionError, match="Unknown function: powertools_json()"):
        # WHEN calling _get_hashed_idempotency_key
        # THEN raise unknown function
        persistence_store._get_hashed_idempotency_key({})


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


def test_handler_raise_idempotency_key_error(persistence_store: DynamoDBPersistenceLayer, lambda_context):
    # GIVEN raise_on_no_idempotency_key is True
    idempotency_config = IdempotencyConfig(event_key_jmespath="idemKey", raise_on_no_idempotency_key=True)

    # WHEN handling the idempotent call
    # AND save_inprogress raises a IdempotencyKeyError
    @idempotent(persistence_store=persistence_store, config=idempotency_config)
    def handler(event, context):
        raise ValueError("Should not be raised")

    # THEN idempotent should re-raise the IdempotencyKeyError
    with pytest.raises(IdempotencyKeyError) as e:
        handler({}, lambda_context)

    assert "No data found to create a hashed idempotency_key" == e.value.args[0]


class MockPersistenceLayer(BasePersistenceLayer):
    def __init__(self, expected_idempotency_key: str):
        self.expected_idempotency_key = expected_idempotency_key
        super(MockPersistenceLayer, self).__init__()

    def _put_record(self, data_record: DataRecord) -> None:
        assert data_record.idempotency_key == self.expected_idempotency_key

    def _update_record(self, data_record: DataRecord) -> None:
        assert data_record.idempotency_key == self.expected_idempotency_key

    def _get_record(self, idempotency_key) -> DataRecord:
        ...

    def _delete_record(self, data_record: DataRecord) -> None:
        ...


def test_idempotent_lambda_event_source(lambda_context):
    # Scenario to validate that we can use the event_source decorator before or after the idempotent decorator
    mock_event = load_event("apiGatewayProxyV2Event.json")
    persistence_layer = MockPersistenceLayer("test-func.lambda_handler#" + hash_idempotency_key(mock_event))
    expected_result = {"message": "Foo"}

    # GIVEN an event_source decorator
    # AND then an idempotent decorator
    @event_source(data_class=APIGatewayProxyEventV2)
    @idempotent(persistence_store=persistence_layer)
    def lambda_handler(event, _):
        assert isinstance(event, APIGatewayProxyEventV2)
        return expected_result

    # WHEN calling the lambda handler
    result = lambda_handler(mock_event, lambda_context)
    # THEN we expect the handler to execute successfully
    assert result == expected_result


def test_idempotent_function():
    # Scenario to validate we can use idempotent_function with any function
    mock_event = {"data": "value"}
    idempotency_key = "test-func.record_handler#" + hash_idempotency_key(mock_event)
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}

    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
    def record_handler(record):
        return expected_result

    # WHEN calling the function
    result = record_handler(record=mock_event)
    # THEN we expect the function to execute successfully
    assert result == expected_result


def test_idempotent_function_arbitrary_args_kwargs():
    # Scenario to validate we can use idempotent_function with a function
    # with an arbitrary number of args and kwargs
    mock_event = {"data": "value"}
    idempotency_key = "test-func.record_handler#" + hash_idempotency_key(mock_event)
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}

    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
    def record_handler(arg_one, arg_two, record, is_record):
        return expected_result

    # WHEN calling the function
    result = record_handler("foo", "bar", record=mock_event, is_record=True)
    # THEN we expect the function to execute successfully
    assert result == expected_result


def test_idempotent_function_invalid_data_kwarg():
    mock_event = {"data": "value"}
    idempotency_key = "test-func.record_handler#" + hash_idempotency_key(mock_event)
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}
    keyword_argument = "payload"

    # GIVEN data_keyword_argument does not match fn signature
    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument=keyword_argument)
    def record_handler(record):
        return expected_result

    # WHEN calling the function
    # THEN we expect to receive a Runtime error
    with pytest.raises(RuntimeError, match=f"Unable to extract '{keyword_argument}'"):
        record_handler(record=mock_event)


def test_idempotent_function_arg_instead_of_kwarg():
    mock_event = {"data": "value"}
    idempotency_key = "test-func.record_handler#" + hash_idempotency_key(mock_event)
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}
    keyword_argument = "record"

    # GIVEN data_keyword_argument matches fn signature
    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument=keyword_argument)
    def record_handler(record):
        return expected_result

    # WHEN calling the function without named argument
    # THEN we expect to receive a Runtime error
    with pytest.raises(RuntimeError, match=f"Unable to extract '{keyword_argument}'"):
        record_handler(mock_event)


def test_idempotent_function_and_lambda_handler(lambda_context):
    # Scenario to validate we can use both idempotent_function and idempotent decorators
    mock_event = {"data": "value"}
    idempotency_key = "test-func.record_handler#" + hash_idempotency_key(mock_event)
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    expected_result = {"message": "Foo"}

    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
    def record_handler(record):
        return expected_result

    persistence_layer = MockPersistenceLayer("test-func.lambda_handler#" + hash_idempotency_key(mock_event))

    @idempotent(persistence_store=persistence_layer)
    def lambda_handler(event, _):
        return expected_result

    # WHEN calling the function
    fn_result = record_handler(record=mock_event)

    # WHEN calling lambda handler
    handler_result = lambda_handler(mock_event, lambda_context)

    # THEN we expect the function and lambda handler to execute successfully
    assert fn_result == expected_result
    assert handler_result == expected_result


def test_idempotent_data_sorting():
    # Scenario to validate same data in different order hashes to the same idempotency key
    data_one = {"data": "test message 1", "more_data": "more data 1"}
    data_two = {"more_data": "more data 1", "data": "test message 1"}
    idempotency_key = "test-func.dummy#" + hash_idempotency_key(data_one)
    # Assertion will happen in MockPersistenceLayer
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    # GIVEN
    @idempotent_function(data_keyword_argument="payload", persistence_store=persistence_layer)
    def dummy(payload):
        return {"message": "hello"}

    # WHEN/THEN assertion will happen at MockPersistenceLayer
    dummy(payload=data_two)


def test_idempotency_disabled_envvar(monkeypatch, lambda_context, persistence_store: DynamoDBPersistenceLayer):
    # Scenario to validate no requests sent to dynamodb table when 'POWERTOOLS_IDEMPOTENCY_DISABLED' is set
    mock_event = {"data": "value"}

    persistence_store.table = MagicMock()

    monkeypatch.setenv("POWERTOOLS_IDEMPOTENCY_DISABLED", "1")

    @idempotent_function(data_keyword_argument="data", persistence_store=persistence_store)
    def dummy(data):
        return {"message": "hello"}

    @idempotent(persistence_store=persistence_store)
    def dummy_handler(event, context):
        return {"message": "hi"}

    dummy(data=mock_event)
    dummy_handler(mock_event, lambda_context)

    assert len(persistence_store.table.method_calls) == 0


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": True}], indirect=True)
def test_idempotent_function_duplicates(
    idempotency_config: IdempotencyConfig, persistence_store: DynamoDBPersistenceLayer
):
    # Scenario to validate the both methods are called
    mock_event = {"data": "value"}
    persistence_store.table = MagicMock()

    @idempotent_function(data_keyword_argument="data", persistence_store=persistence_store, config=idempotency_config)
    def one(data):
        return "one"

    @idempotent_function(data_keyword_argument="data", persistence_store=persistence_store, config=idempotency_config)
    def two(data):
        return "two"

    assert one(data=mock_event) == "one"
    assert two(data=mock_event) == "two"
    assert len(persistence_store.table.method_calls) == 4


def test_invalid_dynamodb_persistence_layer():
    # Scenario constructing a DynamoDBPersistenceLayer with a key_attr matching sort_key_attr should fail
    with pytest.raises(ValueError) as ve:
        DynamoDBPersistenceLayer(
            table_name="Foo",
            key_attr="id",
            sort_key_attr="id",
        )
    # and raise a ValueError
    assert str(ve.value) == "key_attr [id] and sort_key_attr [id] cannot be the same!"


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher for dataclasses")
def test_idempotent_function_dataclasses():
    # Scenario _prepare_data should convert a python dataclasses to a dict
    dataclasses = get_dataclasses_lib()

    @dataclasses.dataclass
    class Foo:
        name: str

    expected_result = {"name": "Bar"}
    data = Foo(name="Bar")
    as_dict = _prepare_data(data)
    assert as_dict == dataclasses.asdict(data)
    assert as_dict == expected_result


def test_idempotent_function_pydantic():
    # Scenario _prepare_data should convert a pydantic to a dict
    class Foo(BaseModel):
        name: str

    expected_result = {"name": "Bar"}
    data = Foo(name="Bar")
    as_dict = _prepare_data(data)
    assert as_dict == data.dict()
    assert as_dict == expected_result


@pytest.mark.parametrize("data", [None, "foo", ["foo"], 1, True, {}])
def test_idempotent_function_other(data):
    # All other data types should be left as is
    assert _prepare_data(data) == data


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher for dataclasses")
def test_idempotent_function_dataclass_with_jmespath():
    # GIVEN
    dataclasses = get_dataclasses_lib()
    config = IdempotencyConfig(event_key_jmespath="transaction_id", use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = "test-func.collect_payment#" + hash_idempotency_key(mock_event["transaction_id"])
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @dataclasses.dataclass
    class Payment:
        customer_id: str
        transaction_id: str

    @idempotent_function(data_keyword_argument="payment", persistence_store=persistence_layer, config=config)
    def collect_payment(payment: Payment):
        return payment.transaction_id

    # WHEN
    payment = Payment(**mock_event)
    result = collect_payment(payment=payment)

    # THEN idempotency key assertion happens at MockPersistenceLayer
    assert result == payment.transaction_id


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher for dataclasses")
def test_idempotent_function_pydantic_with_jmespath():
    # GIVEN
    config = IdempotencyConfig(event_key_jmespath="transaction_id", use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = "test-func.collect_payment#" + hash_idempotency_key(mock_event["transaction_id"])
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    class Payment(BaseModel):
        customer_id: str
        transaction_id: str

    @idempotent_function(data_keyword_argument="payment", persistence_store=persistence_layer, config=config)
    def collect_payment(payment: Payment):
        return payment.transaction_id

    # WHEN
    payment = Payment(**mock_event)
    result = collect_payment(payment=payment)

    # THEN idempotency key assertion happens at MockPersistenceLayer
    assert result == payment.transaction_id


@pytest.mark.parametrize("idempotency_config", [{"use_local_cache": False}], indirect=True)
def test_idempotent_lambda_compound_already_completed(
    idempotency_config: IdempotencyConfig,
    persistence_store_compound: DynamoDBPersistenceLayer,
    lambda_apigw_event,
    timestamp_future,
    hashed_idempotency_key,
    serialized_lambda_response,
    deserialized_lambda_response,
    lambda_context,
):
    """
    Test idempotent decorator having a DynamoDBPersistenceLayer with a compound key
    """

    stubber = stub.Stubber(persistence_store_compound.table.meta.client)
    stubber.add_client_error("put_item", "ConditionalCheckFailedException")
    ddb_response = {
        "Item": {
            "id": {"S": "idempotency#"},
            "sk": {"S": hashed_idempotency_key},
            "expiration": {"N": timestamp_future},
            "data": {"S": serialized_lambda_response},
            "status": {"S": "COMPLETED"},
        }
    }
    expected_params = {
        "TableName": TABLE_NAME,
        "Key": {"id": "idempotency#", "sk": hashed_idempotency_key},
        "ConsistentRead": True,
    }
    stubber.add_response("get_item", ddb_response, expected_params)

    stubber.activate()

    @idempotent(config=idempotency_config, persistence_store=persistence_store_compound)
    def lambda_handler(event, context):
        raise ValueError

    lambda_resp = lambda_handler(lambda_apigw_event, lambda_context)
    assert lambda_resp == deserialized_lambda_response

    stubber.assert_no_pending_responses()
    stubber.deactivate()
