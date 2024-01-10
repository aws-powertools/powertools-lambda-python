import os
import time

from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.idempotency.persistence.redis import RedisCachePersistenceLayer

REDIS_HOST = os.getenv("RedisEndpoint", "")
persistence_layer = RedisCachePersistenceLayer(host=REDIS_HOST, port=6379)
config = IdempotencyConfig(expires_after_seconds=5)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    time_now = time.time()

    return {"time": str(time_now)}
