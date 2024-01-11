import os
import time

from aws_lambda_powertools.utilities.idempotency import (
    idempotent,
)
from aws_lambda_powertools.utilities.idempotency.persistence.redis import RedisCachePersistenceLayer

REDIS_HOST = os.getenv("RedisEndpoint", "")
persistence_layer = RedisCachePersistenceLayer(host=REDIS_HOST, port=6379)


@idempotent(persistence_store=persistence_layer)
def lambda_handler(event, context):
    time.sleep(5)

    return event
