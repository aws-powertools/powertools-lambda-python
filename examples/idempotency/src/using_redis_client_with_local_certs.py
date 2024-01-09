from typing import Any

from redis import Redis

from aws_lambda_powertools.shared.functions import abs_lambda_path
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.idempotency import IdempotencyConfig, idempotent
from aws_lambda_powertools.utilities.idempotency.persistence.redis import (
    RedisCachePersistenceLayer,
)

redis_values: Any = parameters.get_secret("redis_info", transform="json")  # (1)!

default_lambda_path = abs_lambda_path()  # (2)!


redis_client = Redis(
    host=redis_values.get("REDIS_HOST"),
    port=redis_values.get("REDIS_PORT"),
    password=redis_values.get("REDIS_PASSWORD"),
    decode_responses=True,
    socket_timeout=10.0,
    ssl=True,
    retry_on_timeout=True,
    ssl_certfile=f"{default_lambda_path}/redis_user.crt",  # (3)!
    ssl_keyfile=f"{default_lambda_path}/redis_user_private.key",  # (4)!
    ssl_ca_certs=f"{default_lambda_path}/redis_ca.pem",  # (5)!
)

persistence_layer = RedisCachePersistenceLayer(client=redis_client)
config = IdempotencyConfig(
    expires_after_seconds=2 * 60,  # 2 minutes
)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    return {"message": "Hello"}
