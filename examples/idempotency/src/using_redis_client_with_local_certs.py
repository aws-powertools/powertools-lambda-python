from __future__ import annotations

from typing import Any

from redis import Redis

from aws_lambda_powertools.shared.functions import abs_lambda_path
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.idempotency import IdempotencyConfig, idempotent
from aws_lambda_powertools.utilities.idempotency.persistence.cache import (
    CachePersistenceLayer,
)

cache_values: dict[str, Any] = parameters.get_secret("cache_info", transform="json")  # (1)!


redis_client = Redis(
    host=cache_values.get("REDIS_HOST", "localhost"),
    port=cache_values.get("REDIS_PORT", 6379),
    password=cache_values.get("REDIS_PASSWORD"),
    decode_responses=True,
    socket_timeout=10.0,
    ssl=True,
    retry_on_timeout=True,
    ssl_certfile=f"{abs_lambda_path()}/certs/cache_user.crt",  # (2)!
    ssl_keyfile=f"{abs_lambda_path()}/certs/cache_user_private.key",  # (3)!
    ssl_ca_certs=f"{abs_lambda_path()}/certs/cache_ca.pem",  # (4)!
)

persistence_layer = CachePersistenceLayer(client=redis_client)
config = IdempotencyConfig(
    expires_after_seconds=2 * 60,  # 2 minutes
)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    return {"message": "Hello"}
