from redis import Redis

from aws_lambda_powertools.utilities.idempotency import (
    RedisCachePersistenceLayer,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

redis_client = Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

persistence_layer = RedisCachePersistenceLayer(
    client=redis_client,
    in_progress_expiry_attr="in_progress_expiration",
    status_attr="status",
    data_attr="data",
    validation_key_attr="validation",
)


@idempotent(persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return event
