from typing import Any

from redis import Redis

from aws_lambda_powertools.shared.functions import abs_lambda_path
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.idempotency import IdempotencyConfig, idempotent
from aws_lambda_powertools.utilities.idempotency.persistence.redis import (
    RedisCachePersistenceLayer,
)

redis_values: Any = parameters.get_secret("redis_info", transform="json")  # (1)!


redis_client = Redis(
    host=redis_values.get("REDIS_HOST"),
    port=redis_values.get("REDIS_PORT"),
    password=redis_values.get("REDIS_PASSWORD"),
    decode_responses=True,
    socket_timeout=10.0,
    ssl=True,
    retry_on_timeout=True,
    ssl_certfile=f"{abs_lambda_path()}/certs/redis_user.crt",  # (2)!
    ssl_keyfile=f"{abs_lambda_path()}/certs/redis_user_private.key",  # (3)!
    ssl_ca_certs=f"{abs_lambda_path()}/certs/redis_ca.pem",  # (4)!
)

persistence_layer = RedisCachePersistenceLayer(client=redis_client)
config = IdempotencyConfig(
    expires_after_seconds=2 * 60,  # 2 minutes
)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    return {"message": "Hello"}
