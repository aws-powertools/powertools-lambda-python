from __future__ import annotations

from typing import Any

from glide import BackoffStrategy, GlideClient, GlideClientConfiguration, NodeAddress, ServerCredentials

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.idempotency import IdempotencyConfig, idempotent
from aws_lambda_powertools.utilities.idempotency.persistence.cache import (
    CachePersistenceLayer,
)

cache_values: dict[str, Any] = parameters.get_secret("cache_info", transform="json")  # (1)!

client_config = GlideClientConfiguration(
    addresses=[
        NodeAddress(
            host=cache_values.get("CACHE_HOST", "localhost"),
            port=cache_values.get("CACHE_PORT", 6379),
        ),
    ],
    credentials=ServerCredentials(
        password=cache_values.get("CACHE_PASSWORD", ""),
    ),
    request_timeout=10,
    use_tls=True,
    reconnect_strategy=BackoffStrategy(num_of_retries=10, factor=2, exponent_base=1),
)
valkey_client = GlideClient.create(config=client_config)

persistence_layer = CachePersistenceLayer(client=valkey_client)  # type: ignore[arg-type]
config = IdempotencyConfig(
    expires_after_seconds=2 * 60,  # 2 minutes
)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    return {"message": "Hello"}
