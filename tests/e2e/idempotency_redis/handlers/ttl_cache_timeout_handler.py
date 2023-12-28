import os
import time

from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig,
    RedisCachePersistenceLayer,
    idempotent,
)

REDIS_HOST = os.getenv("RedisEndpoint", "")
persistence_layer = RedisCachePersistenceLayer(host=REDIS_HOST, port=6379, ssl=True)
config = IdempotencyConfig(expires_after_seconds=1)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    sleep_time: int = event.get("sleep") or 0
    time.sleep(sleep_time)

    return event
