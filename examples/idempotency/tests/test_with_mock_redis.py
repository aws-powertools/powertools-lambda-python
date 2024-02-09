from dataclasses import dataclass

import pytest
from mock_redis import MockRedis

from aws_lambda_powertools.utilities.idempotency import (
    idempotent,
)
from aws_lambda_powertools.utilities.idempotency.persistence.redis import (
    RedisCachePersistenceLayer,
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


def test_idempotent_lambda(lambda_context):
    # Init the Mock redis client
    redis_client = MockRedis(decode_responses=True)
    # Establish persistence layer using the mock redis client
    persistence_layer = RedisCachePersistenceLayer(client=redis_client)

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
