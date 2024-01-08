import os
import uuid

from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig,
    RedisCachePersistenceLayer,
    idempotent,
)

REDIS_HOST = os.getenv("RedisEndpoint", "")
persistence_layer = RedisCachePersistenceLayer(host=REDIS_HOST, port=6379)
config = IdempotencyConfig(event_key_jmespath='headers."X-Idempotency-Key"', use_local_cache=True)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    return {"request": str(uuid.uuid4())}
