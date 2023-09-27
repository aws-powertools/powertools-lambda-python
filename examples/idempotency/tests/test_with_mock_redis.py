import time as t
from dataclasses import dataclass

import pytest

from aws_lambda_powertools.utilities.idempotency import (
    RedisCachePersistenceLayer,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

        def get_remaining_time_in_millis(self) -> int:
            return 1000

    return LambdaContext()


# Mock redis class that includes all operations we used in Idempotency
class MockRedis:
    def __init__(self, decode_responses, cache: dict = None, **kwargs):
        self.cache = cache or {}
        self.expire_dict = {}
        self.decode_responses = decode_responses
        self.acl = {}
        self.username = ""

    def hset(self, name, mapping):
        self.expire_dict.pop(name, {})
        self.cache[name] = mapping

    def from_url(self, url: str):
        pass

    def expire(self, name, time):
        self.expire_dict[name] = t.time() + time

    # return {} if no match
    def hgetall(self, name):
        if self.expire_dict.get(name, t.time() + 1) < t.time():
            self.cache.pop(name, {})
        return self.cache.get(name, {})

    def get_connection_kwargs(self):
        return {"decode_responses": self.decode_responses}

    def auth(self, username, **kwargs):
        self.username = username

    def delete(self, name):
        self.cache.pop(name, {})


def test_idempotent_lambda(lambda_context):
    # Init the Mock redis client
    redis_client = MockRedis(decode_responses=True)
    # Establish persistence layer using the mock redis client
    persistence_layer = RedisCachePersistenceLayer(connection=redis_client)

    # setup idempotent with redis persistence layer
    @idempotent(persistence_store=persistence_layer)
    def lambda_handler(event: dict, context: LambdaContext):
        print("expensive operation")
        return {
            "payment_id": 12345,
            "message": "success",
            "statusCode": 200,
        }

    # Inovke the sim lambda handler
    result = lambda_handler({"testkey": "testvalue"}, lambda_context)
    assert result["payment_id"] == 12345
