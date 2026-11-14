import pytest
from botocore.stub import Stubber

from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent
from aws_lambda_powertools.utilities.idempotency.exceptions import IdempotencyAlreadyInProgressError


@pytest.fixture(params=[None, "sk", "record_key"])
def record_store(request, config):
    return DynamoDBPersistenceLayer(
        table_name="TEST_TABLE",
        boto_config=config,
        sort_key_attr=request.param,
        static_pk_value="shared-partition",
    )


def stored_item(store, key, expiry, status="COMPLETED"):
    item = {
        "id": {"S": "shared-partition" if store.sort_key_attr else key},
        "expiration": {"N": expiry},
        "status": {"S": status},
        "data": {"S": '{"message": "stored"}'},
    }
    if store.sort_key_attr:
        item[store.sort_key_attr] = {"S": key}
    return item


def stub_existing_record(stubber, store, item, source):
    if source == "condition":
        stubber.add_client_error("put_item", "ConditionalCheckFailedException", modeled_fields={"Item": item})
    else:
        stubber.add_client_error("put_item", "ConditionalCheckFailedException")
        key = {"id": item["id"]}
        if store.sort_key_attr:
            key[store.sort_key_attr] = item[store.sort_key_attr]
        stubber.add_response(
            "get_item",
            {"Item": item},
            {
                "TableName": "TEST_TABLE",
                "Key": key,
                "ConsistentRead": True,
            },
        )


@pytest.mark.parametrize("source", ["condition", "get_item"])
@pytest.mark.parametrize("use_local_cache", [False, True])
def test_response_hook_receives_record_key(
    record_store,
    source,
    use_local_cache,
    lambda_apigw_event,
    lambda_context,
    timestamp_future,
    hashed_idempotency_key,
    default_jmespath,
):
    keys = []

    def response_hook(response, record):
        keys.append((record.idempotency_key, record.sort_key))
        return response

    config = IdempotencyConfig(
        event_key_jmespath=default_jmespath,
        use_local_cache=use_local_cache,
        response_hook=response_hook,
    )

    @idempotent(config=config, persistence_store=record_store)
    def lambda_handler(event, context):
        pytest.fail("A stored response must bypass the handler")

    item = stored_item(record_store, hashed_idempotency_key, timestamp_future)
    with Stubber(record_store.client) as stubber:
        stub_existing_record(stubber, record_store, item, source)
        assert lambda_handler(lambda_apigw_event, lambda_context) == {"message": "stored"}
        stubber.assert_no_pending_responses()

    expected_sort_key = hashed_idempotency_key if record_store.sort_key_attr else None
    assert keys == [(hashed_idempotency_key, expected_sort_key)]


@pytest.mark.parametrize("source", ["condition", "get_item"])
def test_stored_response_is_replayed_from_local_cache(
    record_store,
    source,
    lambda_apigw_event,
    lambda_context,
    timestamp_future,
    hashed_idempotency_key,
    default_jmespath,
):
    config = IdempotencyConfig(event_key_jmespath=default_jmespath, use_local_cache=True)

    @idempotent(config=config, persistence_store=record_store)
    def lambda_handler(event, context):
        pytest.fail("A stored response must bypass the handler")

    item = stored_item(record_store, hashed_idempotency_key, timestamp_future)
    with Stubber(record_store.client) as stubber:
        stub_existing_record(stubber, record_store, item, source)
        assert lambda_handler(lambda_apigw_event, lambda_context) == {"message": "stored"}
        # No more DynamoDB requests are stubbed: the second invocation must use the cache.
        assert lambda_handler(lambda_apigw_event, lambda_context) == {"message": "stored"}
        stubber.assert_no_pending_responses()


@pytest.mark.parametrize("source", ["condition", "get_item"])
def test_in_progress_error_identifies_record_key(
    record_store,
    source,
    lambda_apigw_event,
    lambda_context,
    timestamp_future,
    hashed_idempotency_key,
    default_jmespath,
):
    config = IdempotencyConfig(event_key_jmespath=default_jmespath)

    @idempotent(config=config, persistence_store=record_store)
    def lambda_handler(event, context):
        pytest.fail("An in-progress invocation must bypass the handler")

    item = stored_item(record_store, hashed_idempotency_key, timestamp_future, status="INPROGRESS")
    with Stubber(record_store.client) as stubber:
        stub_existing_record(stubber, record_store, item, source)
        with pytest.raises(IdempotencyAlreadyInProgressError) as exc:
            lambda_handler(lambda_apigw_event, lambda_context)
        assert f"{default_jmespath}={hashed_idempotency_key}" in str(exc.value)
        stubber.assert_no_pending_responses()
