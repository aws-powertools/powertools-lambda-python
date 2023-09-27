from aws_lambda_powertools.utilities.idempotency import (
    RedisCachePersistenceLayer,
    RedisConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

config = RedisConfig(host="localhost", port=6379, mode="standalone")

persistence_layer = RedisCachePersistenceLayer(
    config=config,
    in_progress_expiry_attr="in_progress_expiration",
    status_attr="status",
    data_attr="data",
    validation_key_attr="validation",
)


@idempotent(persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return event
