from __future__ import annotations

from typing_extensions import deprecated

from aws_lambda_powertools.utilities.idempotency.persistence.cache import (
    CacheClientProtocol,
    CacheConnection,
    CachePersistenceLayer,
)

__all__ = [
    "RedisCachePersistenceLayer",
    "RedisClientProtocol",
    "RedisConnection",
]


@deprecated("RedisPersistenceLayer will be removed in v4.0.0. Please use CacheProtocol instead.")
class RedisClientProtocol(CacheClientProtocol): ...


@deprecated("RedisConnection will be removed in v4.0.0. Please use CacheConnection instead.")
class RedisConnection(CacheConnection): ...


@deprecated("RedisCachePersistenceLayer will be removed in v4.0.0. Please use CachePersistenceLayer instead.")
class RedisCachePersistenceLayer(CachePersistenceLayer): ...
