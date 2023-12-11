import copy

import pytest
from testcontainers.redis import RedisContainer

from aws_lambda_powertools.utilities.idempotency import RedisCachePersistenceLayer
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyAlreadyInProgressError,
    IdempotencyItemAlreadyExistsError,
    IdempotencyItemNotFoundError,
    IdempotencyPersistenceLayerError,
)
from aws_lambda_powertools.utilities.idempotency.idempotency import (
    idempotent,
    idempotent_function,
)


@pytest.fixture
def redis_container_image():
    return "public.ecr.aws/docker/library/redis:7.2-alpine"


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


# test basic
def test_idempotent_function_and_lambda_handler_redis_basic(
    lambda_context,
    redis_container_image,
):
    with RedisContainer(image=redis_container_image) as redis_container:
        redis_client = redis_container.get_client()
        mock_event = {"data": "value"}
        persistence_layer = RedisCachePersistenceLayer(client=redis_client)
        expected_result = {"message": "Foo"}

        @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
        def record_handler(record):
            return expected_result

        @idempotent(persistence_store=persistence_layer)
        def lambda_handler(event, context):
            return expected_result

        # WHEN calling the function
        fn_result = record_handler(record=mock_event)
        # WHEN calling lambda handler
        handler_result = lambda_handler(mock_event, lambda_context)
        # THEN we expect the function and lambda handler to execute successfully
        assert fn_result == expected_result
        assert handler_result == expected_result


def test_idempotent_function_and_lambda_handler_redis_cache(
    lambda_context,
    redis_container_image,
):
    with RedisContainer(image=redis_container_image) as redis_container:
        redis_client = redis_container.get_client()
        mock_event = {"data": "value2"}
        persistence_layer = RedisCachePersistenceLayer(client=redis_client)
        result = {"message": "Foo"}
        expected_result = copy.deepcopy(result)

        @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
        def record_handler(record):
            return result

        @idempotent(persistence_store=persistence_layer)
        def lambda_handler(event, context):
            return result

        # WHEN calling the function
        fn_result = record_handler(record=mock_event)
        # WHEN calling lambda handler
        handler_result = lambda_handler(mock_event, lambda_context)
        # THEN we expect the function and lambda handler to execute successfully
        assert fn_result == expected_result
        assert handler_result == expected_result

        # modify the return to check if idem cache works
        result = {"message": "Bar"}
        fn_result2 = record_handler(record=mock_event)
        # Second time calling lambda handler, test if same result
        handler_result2 = lambda_handler(mock_event, lambda_context)
        assert fn_result2 == expected_result
        assert handler_result2 == expected_result

        # modify the mock event to check if we got updated result
        mock_event = {"data": "value3"}
        fn_result3 = record_handler(record=mock_event)
        # thrid time calling lambda handler, test if result updated
        handler_result3 = lambda_handler(mock_event, lambda_context)
        assert fn_result3 == result
        assert handler_result3 == result


# test idem-inprogress
def test_idempotent_lambda_redis_in_progress(
    lambda_context,
    redis_container_image,
):
    """
    Test idempotent decorator where lambda_handler is already processing an event with matching event key
    """
    with RedisContainer(image=redis_container_image) as redis_container:
        redis_client = redis_container.get_client()

        mock_event = {"data": "value4"}
        persistence_store = RedisCachePersistenceLayer(client=redis_client)
        lambda_response = {"foo": "bar"}

        @idempotent(persistence_store=persistence_store)
        def lambda_handler(event, context):
            return lambda_response

        # register the context first
        lambda_handler(mock_event, lambda_context)
        # save additional to in_progress
        mock_event = {"data": "value7"}
        try:
            persistence_store.save_inprogress(mock_event, 10000)
        except IdempotencyItemAlreadyExistsError:
            pass

        with pytest.raises(IdempotencyAlreadyInProgressError):
            lambda_handler(mock_event, lambda_context)


# test -remove
def test_idempotent_lambda_redis_delete(
    lambda_context,
    redis_container_image,
):
    with RedisContainer(image=redis_container_image) as redis_container:
        redis_client = redis_container.get_client()
        mock_event = {"data": "test_delete"}
        persistence_layer = RedisCachePersistenceLayer(client=redis_client)
        result = {"message": "Foo"}

        @idempotent(persistence_store=persistence_layer)
        def lambda_handler(event, context):
            return result

        # first run is just to populate function infos for deletion.
        # delete_record won't work if the function was not run yet. bug maybe?
        handler_result = lambda_handler(mock_event, lambda_context)
        # delete what's might be dirty data
        persistence_layer.delete_record(mock_event, IdempotencyItemNotFoundError)
        # run second time to ensure clean result
        handler_result = lambda_handler(mock_event, lambda_context)
        assert handler_result == result
        persistence_layer.delete_record(mock_event, IdempotencyItemNotFoundError)
        # delete the idem and handler should output new result
        result = {"message": "Foo2"}
        handler_result2 = lambda_handler(mock_event, lambda_context)

        assert handler_result2 == result


def test_idempotent_lambda_redis_credential(lambda_context, redis_container_image):
    with RedisContainer(image=redis_container_image) as redis_container:
        redis_client = redis_container.get_client()

        pwd = "terriblePassword"
        usr = "test_acl_denial"
        redis_client.acl_setuser(
            username=usr,
            enabled=True,
            passwords="+" + pwd,
            keys="*",
            commands=["+hgetall", "-set"],
        )
        redis_client.auth(password=pwd, username=usr)

    @idempotent(persistence_store=RedisCachePersistenceLayer(client=redis_client))
    def lambda_handler(event, _):
        return True

    with pytest.raises(IdempotencyPersistenceLayerError):
        lambda_handler("test_Acl", lambda_context)
