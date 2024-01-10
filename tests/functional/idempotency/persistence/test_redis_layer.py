# ruff: noqa
import copy
import json
import time as t

import pytest
from unittest.mock import patch

from aws_lambda_powertools.utilities.idempotency.persistence.redis import (
    RedisCachePersistenceLayer,
)
import datetime

from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    STATUS_CONSTANTS,
    DataRecord,
)

from unittest import mock
from multiprocessing import Process, Manager, Lock
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyAlreadyInProgressError,
    IdempotencyItemAlreadyExistsError,
    IdempotencyItemNotFoundError,
    IdempotencyPersistenceConnectionError,
    IdempotencyPersistenceConfigError,
    IdempotencyPersistenceConsistencyError,
    IdempotencyValidationError,
)
from aws_lambda_powertools.utilities.idempotency.idempotency import (
    idempotent,
    idempotent_function,
    IdempotencyConfig,
)

redis_badhost = "badhost"


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


class RedisExceptions:
    class RedisClusterException(Exception):
        "mock cluster exception"

    class RedisError(Exception):
        "mock redis exception"

    class ConnectionError(Exception):
        "mock connection exception"


class MockRedisBase:
    # use this class to test no get_connection_kwargs error
    exceptions = RedisExceptions

    def __call__(self, *args, **kwargs):
        if kwargs.get("host") == redis_badhost:
            raise self.exceptions.ConnectionError
        self.__dict__.update(kwargs)
        return self

    @property
    def Redis(self):
        self.mode = "standalone"
        return self

    @property
    def cluster(self):
        return self

    @property
    def RedisCluster(self):
        self.mode = "cluster"
        return self

    # use this to mimic Redis error
    def close(self):
        self.closed = True


class MockRedis(MockRedisBase):
    def __init__(self, cache: dict = None, mock_latency_ms: int = 0, **kwargs):
        self.cache = cache or {}
        self.expire_dict = {}
        self.acl = {}
        self.username = ""
        self.mode = ""
        self.url = ""
        self.__dict__.update(kwargs)
        self.closed = False
        self.mock_latency_ms = mock_latency_ms
        self.nx_lock = Lock()
        super(MockRedis, self).__init__()

    # check_closed is called before every mock redis operation
    def check_closed(self):
        if self.mock_latency_ms != 0:
            t.sleep(self.mock_latency_ms / 1000)
        if self.closed == False:
            return
        if self.mode == "cluster":
            raise self.exceptions.RedisClusterException
        raise self.exceptions.RedisError

    def from_url(self, url: str):
        self.url = url
        return self

    # not covered by test yet.
    def expire(self, name, time):
        self.check_closed()
        if time != 0:
            self.expire_dict[name] = t.time() + time

    def auth(self, username, **kwargs):
        self.username = username

    def delete(self, name):
        self.check_closed()
        self.cache.pop(name, {})

    # return None if nx failed, return True if done
    def set(self, name, value, ex: int = 0, nx: bool = False):
        # expire existing
        self.check_closed()
        if self.expire_dict.get(name, t.time() + 1) < t.time():
            self.cache.pop(name, {})

        if isinstance(value, str):
            value = value.encode()

        # nx logic, acquire a lock for multiprocessing safety
        with self.nx_lock:
            # key exist, nx mode will just return None
            if name in self.cache and nx:
                return None

            # key doesn't exist, set the key
            self.cache[name] = value
            self.expire(name, ex)
        return True

    # return None if not found
    def get(self, name: str):
        self.check_closed()
        if self.expire_dict.get(name, t.time() + 1) < t.time():
            self.cache.pop(name, {})

        resp = self.cache.get(name, None)

        return resp


@pytest.fixture
def persistence_store_standalone_redis_no_decode():
    redis_client = MockRedis(
        host="localhost",
        port="63005",
    )
    return RedisCachePersistenceLayer(client=redis_client)


@pytest.fixture
def persistence_store_standalone_redis():
    redis_client = MockRedis(
        host="localhost",
        port="63005",
    )
    return RedisCachePersistenceLayer(client=redis_client)


@pytest.fixture
def orphan_record():
    return DataRecord(
        idempotency_key="test_orphan_key",
        status=STATUS_CONSTANTS["INPROGRESS"],
        in_progress_expiry_timestamp=int(datetime.datetime.now().timestamp() * 1000 - 1),
    )


@pytest.fixture
def valid_record():
    return DataRecord(
        idempotency_key="test_orphan_key",
        status=STATUS_CONSTANTS["INPROGRESS"],
        in_progress_expiry_timestamp=int(datetime.datetime.now().timestamp() * 1000 + 1000),
    )


@mock.patch("aws_lambda_powertools.utilities.idempotency.persistence.redis.redis", MockRedis())
def test_redis_connection_standalone():
    # when RedisCachePersistenceLayer is init with the following params
    redis_conf = {
        "host": "host",
        "port": "port",
        "mode": "standalone",
        "username": "redis_user",
        "password": "redis_pass",
        "db_index": "db_index",
    }
    layer = RedisCachePersistenceLayer(**redis_conf)
    redis_conf["db"] = redis_conf["db_index"]
    redis_conf.pop("db_index")
    # then these params should be passed down to mock Redis identically
    for k, v in redis_conf.items():
        assert layer.client.__dict__.get(k) == v


@mock.patch("aws_lambda_powertools.utilities.idempotency.persistence.redis.redis", MockRedis())
def test_redis_connection_cluster():
    # when RedisCachePersistenceLayer is init with the following params
    redis_conf = {
        "host": "host",
        "port": "port",
        "mode": "cluster",
        "username": "redis_user",
        "password": "redis_pass",
        "db_index": "db_index",
    }
    layer = RedisCachePersistenceLayer(**redis_conf)
    redis_conf["db"] = None
    redis_conf.pop("db_index")

    # then these params should be passed down to mock Redis identically
    for k, v in redis_conf.items():
        assert layer.client.__dict__.get(k) == v


@mock.patch("aws_lambda_powertools.utilities.idempotency.persistence.redis.redis", MockRedis())
def test_redis_connection_conn_error():
    # when RedisCachePersistenceLayer is init with a bad host
    # then should raise IdempotencyRedisConnectionError
    with pytest.raises(IdempotencyPersistenceConnectionError):
        RedisCachePersistenceLayer(host=redis_badhost)


@mock.patch("aws_lambda_powertools.utilities.idempotency.persistence.redis.redis", MockRedis())
def test_redis_connection_conf_error():
    # when RedisCachePersistenceLayer is init with a not_supported_mode in mode param
    # then should raise IdempotencyRedisClientConfigError
    with pytest.raises(IdempotencyPersistenceConfigError):
        RedisCachePersistenceLayer(mode="not_supported_mode")


@mock.patch("aws_lambda_powertools.utilities.idempotency.persistence.redis.redis", MockRedis())
def test_redis_key_error():
    # when RedisCachePersistenceLayer is trying to get a non-exist key
    # then should raise IdempotencyItemNotFoundError
    with pytest.raises(IdempotencyItemNotFoundError):
        layer = RedisCachePersistenceLayer(host="host")
        layer._get_record(idempotency_key="not_exist")


@mock.patch("aws_lambda_powertools.utilities.idempotency.persistence.redis.redis", MockRedis())
def test_redis_key_corrupted():
    # when RedisCachePersistenceLayer got a non-json formatted record
    # then should raise IdempotencyOrphanRecordError
    with pytest.raises(IdempotencyPersistenceConsistencyError):
        layer = RedisCachePersistenceLayer(url="sample_url")
        layer.client.set("corrupted_json", "not_json_string")
        layer._get_record(idempotency_key="corrupted_json")


@mock.patch("aws_lambda_powertools.utilities.idempotency.persistence.redis.redis", MockRedis())
def test_redis_orphan_record(orphan_record, valid_record):
    layer = RedisCachePersistenceLayer(host="host")
    # Given orphan record exist
    layer._put_in_progress_record(orphan_record)
    # When we are tyring to update the record
    layer._put_in_progress_record(valid_record)
    # Then orphan record will be overwritten
    assert (
        layer._get_record(valid_record.idempotency_key).in_progress_expiry_timestamp
        == valid_record.in_progress_expiry_timestamp
    )


@mock.patch("aws_lambda_powertools.utilities.idempotency.persistence.redis.redis", MockRedis())
def test_redis_orphan_record_lock(orphan_record, valid_record):
    layer = RedisCachePersistenceLayer(host="host")
    # Given orphan record exist, lock also exist
    layer._put_in_progress_record(orphan_record)
    layer.client.set("test_orphan_key:lock", "True")
    #  when trying to overwrite the record
    # Then we should raise IdempotencyItemAlreadyExistsError
    with pytest.raises(IdempotencyItemAlreadyExistsError):
        layer._put_in_progress_record(valid_record)
    # And the record should not be overwritten
    assert (
        layer._get_record(valid_record.idempotency_key).in_progress_expiry_timestamp
        == orphan_record.in_progress_expiry_timestamp
    )


@mock.patch("aws_lambda_powertools.utilities.idempotency.persistence.redis.redis", MockRedis())
def test_redis_error_in_progress(valid_record):
    layer = RedisCachePersistenceLayer(host="host", mode="standalone")
    layer.client.close()
    # given a Redis is returning RedisError
    # when trying to save inprogress
    # then layer should raise RedisExceptions.RedisError
    with pytest.raises(RedisExceptions.RedisError):
        layer._put_in_progress_record(valid_record)


@mock.patch("aws_lambda_powertools.utilities.idempotency.persistence.redis.redis", MockRedis())
def test_item_to_datarecord_conversion(valid_record):
    layer = RedisCachePersistenceLayer(host="host", mode="standalone")
    item = {
        "status": STATUS_CONSTANTS["INPROGRESS"],
        layer.in_progress_expiry_attr: int(datetime.datetime.now().timestamp() * 1000),
    }
    # given we have a dict of datarecord
    # when calling _item_to_data_record
    record = layer._item_to_data_record(idempotency_key="abc", item=item)
    # then all valid fields in dict should be copied into data_record
    assert record.idempotency_key == "abc"
    assert record.status == STATUS_CONSTANTS["INPROGRESS"]
    assert record.in_progress_expiry_timestamp == item[layer.in_progress_expiry_attr]


def test_idempotent_function_and_lambda_handler_redis_basic(
    persistence_store_standalone_redis: RedisCachePersistenceLayer,
    lambda_context,
):
    mock_event = {"data": "value"}
    persistence_layer = persistence_store_standalone_redis
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
    persistence_store_standalone_redis: RedisCachePersistenceLayer,
    lambda_context,
):
    mock_event = {"data": "value2"}
    persistence_layer = persistence_store_standalone_redis
    result = {"message": "Foo"}
    expected_result = copy.deepcopy(result)

    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
    def record_handler(record):
        return result

    @idempotent(persistence_store=persistence_layer)
    def lambda_handler(event, context):
        return result

    # WHEN calling the function and handler with idempotency
    fn_result = record_handler(record=mock_event)
    handler_result = lambda_handler(mock_event, lambda_context)
    # THEN we expect the function and lambda handler to execute successfully
    assert fn_result == expected_result
    assert handler_result == expected_result

    result = {"message": "Bar"}
    # Given idempotency record already in Redis
    # When we modified the actual function output and run the second time
    fn_result2 = record_handler(record=mock_event)
    handler_result2 = lambda_handler(mock_event, lambda_context)
    # Then the result should be the same as first time
    assert fn_result2 == expected_result
    assert handler_result2 == expected_result

    # Given idempotency record already in Redis
    # When we modified the actual function output and use a different payload
    mock_event = {"data": "value3"}
    fn_result3 = record_handler(record=mock_event)
    handler_result3 = lambda_handler(mock_event, lambda_context)
    # Then the result should be the actual function output
    assert fn_result3 == result
    assert handler_result3 == result


def test_idempotent_function_and_lambda_handler_redis_event_key(
    persistence_store_standalone_redis: RedisCachePersistenceLayer,
    lambda_context,
):
    mock_event = {"body": '{"user_id":"xyz","time":"1234"}'}
    persistence_layer = persistence_store_standalone_redis
    result = {"message": "Foo"}
    expected_result = copy.deepcopy(result)
    config = IdempotencyConfig(event_key_jmespath='powertools_json(body).["user_id"]')

    @idempotent(persistence_store=persistence_layer, config=config)
    def lambda_handler(event, context):
        return result

    # WHEN calling the function and handler with idempotency and event_key_jmespath config to only verify user_id
    handler_result = lambda_handler(mock_event, lambda_context)
    # THEN we expect the function and lambda handler to execute successfully
    assert handler_result == expected_result

    result = {"message": "Bar"}
    mock_event = {"body": '{"user_id":"xyz","time":"2345"}'}
    # Given idempotency record already in Redis
    # When we modified the actual function output, time in mock event and run the second time
    handler_result2 = lambda_handler(mock_event, lambda_context)
    # Then the result should be the same as first time
    assert handler_result2 == expected_result


def test_idempotent_function_and_lambda_handler_redis_validation(
    persistence_store_standalone_redis: RedisCachePersistenceLayer,
    lambda_context,
):
    mock_event = {"user_id": "xyz", "time": "1234"}
    persistence_layer = persistence_store_standalone_redis
    result = {"message": "Foo"}
    config = IdempotencyConfig(event_key_jmespath="user_id", payload_validation_jmespath="time")

    @idempotent(persistence_store=persistence_layer, config=config)
    def lambda_handler(event, context):
        return result

    # WHEN calling the function and handler with idempotency and event_key_jmespath,payload_validation_jmespath
    lambda_handler(mock_event, lambda_context)
    # THEN we expect the function and lambda handler to execute successfully

    result = {"message": "Bar"}
    mock_event = {"user_id": "xyz", "time": "2345"}
    # Given idempotency record already in Redis
    # When we modified the payload where validation is on and invoke again.
    # Then should raise IdempotencyValidationError
    with pytest.raises(IdempotencyValidationError):
        lambda_handler(mock_event, lambda_context)


def test_idempotent_function_and_lambda_handler_redis_basic_no_decode(
    persistence_store_standalone_redis_no_decode: RedisCachePersistenceLayer,
    lambda_context,
):
    # GIVEN redis client passed in has decode_responses=False
    mock_event = {"data": "value-nodecode"}
    persistence_layer = persistence_store_standalone_redis_no_decode
    result = {"message": "Foo"}
    expected_result = copy.deepcopy(result)

    @idempotent_function(persistence_store=persistence_layer, data_keyword_argument="record")
    def record_handler(record):
        return result

    @idempotent(persistence_store=persistence_layer)
    def lambda_handler(event, context):
        return result

    # WHEN calling the function and handler with idempotency
    fn_result = record_handler(record=mock_event)
    handler_result = lambda_handler(mock_event, lambda_context)
    # THEN we expect the function and lambda handler to execute successfully
    assert fn_result == expected_result
    assert handler_result == expected_result

    result = {"message": "Bar"}
    # Given idempotency record already in Redis
    # When we modified the actual function output and run the second time
    fn_result2 = record_handler(record=mock_event)
    handler_result2 = lambda_handler(mock_event, lambda_context)
    # Then the result should be the same as first time
    assert fn_result2 == expected_result
    assert handler_result2 == expected_result

    # Given idempotency record already in Redis
    # When we modified the actual function output and use a different payload
    mock_event = {"data": "value3"}
    fn_result3 = record_handler(record=mock_event)
    handler_result3 = lambda_handler(mock_event, lambda_context)
    # Then the result should be the actual function output
    assert fn_result3 == result
    assert handler_result3 == result


def test_idempotent_lambda_redis_in_progress(
    persistence_store_standalone_redis: RedisCachePersistenceLayer,
    lambda_context,
):
    """
    Test idempotent decorator where lambda_handler is already processing an event with matching event key
    """

    mock_event = {"data": "value4"}
    persistence_store = persistence_store_standalone_redis
    lambda_response = {"foo": "bar"}

    @idempotent(persistence_store=persistence_store)
    def lambda_handler(event, context):
        return lambda_response

    # Given in_progress idempotency record already in Redis
    lambda_handler(mock_event, lambda_context)
    mock_event = {"data": "value7"}
    try:
        persistence_store.save_inprogress(mock_event, 1000)
    except IdempotencyItemAlreadyExistsError:
        pass
    # when invoking with same payload
    # then should raise IdempotencyAlreadyInProgressError
    with pytest.raises(IdempotencyAlreadyInProgressError):
        lambda_handler(mock_event, lambda_context)


def test_idempotent_lambda_redis_delete(
    persistence_store_standalone_redis: RedisCachePersistenceLayer,
    lambda_context,
):
    mock_event = {"data": "test_delete"}
    persistence_layer = persistence_store_standalone_redis
    result = {"message": "Foo"}

    @idempotent(persistence_store=persistence_layer)
    def lambda_handler(event, _):
        return result

    handler_result = lambda_handler(mock_event, lambda_context)
    assert handler_result == result
    # Given the idempotency record from the first run deleted
    persistence_layer.delete_record(mock_event, IdempotencyItemNotFoundError)
    result = {"message": "Foo2"}
    # When lambda hander run for the second time
    handler_result2 = lambda_handler(mock_event, lambda_context)

    # Then lambda handler should return a actual function output
    assert handler_result2 == result


def test_redis_orphan_record_race_condition(lambda_context):
    redis_client = MockRedis(
        host="localhost",
        port="63005",
        mock_latency_ms=50,
    )
    manager = Manager()
    # use a thread safe dict
    redis_client.expire_dict = manager.dict()
    redis_client.cache = manager.dict()
    # given a mock redis client with latency, orphan record exists
    layer = RedisCachePersistenceLayer(client=redis_client)

    mock_event = {"data": "value4"}
    lambda_response = {"foo": "bar"}

    @idempotent(persistence_store=layer)
    def lambda_handler(event, context):
        print("lambda executed")
        if redis_client.cache.get("exec_count", None) != None:
            redis_client.cache["exec_count"] += 1
        return lambda_response

    # run handler for the first time to create a valid record in cache
    lambda_handler(mock_event, lambda_context)
    # modify the cache expiration to create the orphan record
    for key, item in redis_client.cache.items():
        json_dict = json.loads(item)
        json_dict["expiration"] = int(t.time()) - 4000
        redis_client.cache[key] = json.dumps(json_dict).encode()
    # Given orphan idempotency record with same payload already in Redis
    # When running two lambda handler at the same time
    redis_client.cache["exec_count"] = 0
    p1 = Process(target=lambda_handler, args=(mock_event, lambda_context))
    p2 = Process(target=lambda_handler, args=(mock_event, lambda_context))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    # Then only one handler will actually run
    assert redis_client.cache["exec_count"] == 1


# race condition on empty record
def test_redis_race_condition(lambda_context):
    redis_client = MockRedis(
        host="localhost",
        port="63005",
        mock_latency_ms=50,
    )
    manager = Manager()
    # use a thread safe dict
    redis_client.expire_dict = manager.dict()
    redis_client.cache = manager.dict()
    # given a mock redis client with latency, orphan record exists
    layer = RedisCachePersistenceLayer(client=redis_client)

    mock_event = {"data": "value4"}
    lambda_response = {"foo": "bar"}

    @idempotent(persistence_store=layer)
    def lambda_handler(event, context):
        print("lambda executed")
        if redis_client.cache.get("exec_count", None) != None:
            redis_client.cache["exec_count"] += 1
        return lambda_response

    # When running two lambda handler at the same time
    redis_client.cache["exec_count"] = 0
    p1 = Process(target=lambda_handler, args=(mock_event, lambda_context))
    p2 = Process(target=lambda_handler, args=(mock_event, lambda_context))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    # Then only one handler will actually run
    assert redis_client.cache["exec_count"] == 1
