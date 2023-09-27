"""
Utility for adding idempotency to lambda functions
"""

from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    BasePersistenceLayer,
)
from aws_lambda_powertools.utilities.idempotency.persistence.dynamodb import (
    DynamoDBPersistenceLayer,
)

# import RedisCachePersistenceLayer here mean we will need redis as a required lib? Do we want to make it optional?
from aws_lambda_powertools.utilities.idempotency.persistence.redis import (
    RedisCachePersistenceLayer,
    RedisConfig,
)

from .idempotency import IdempotencyConfig, idempotent, idempotent_function

__all__ = (
    "DynamoDBPersistenceLayer",
    "BasePersistenceLayer",
    "idempotent",
    "idempotent_function",
    "IdempotencyConfig",
    "RedisCachePersistenceLayer",
    "RedisConfig",
)
