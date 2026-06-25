"""
Persistence layers for the Circuit Breaker utility.
"""

from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.base import CircuitBreakerPersistenceLayer
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.dynamodb import (
    CircuitBreakerDynamoDBPersistence,
)
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.record import CircuitStateRecord

__all__ = (
    "CircuitBreakerPersistenceLayer",
    "CircuitBreakerDynamoDBPersistence",
    "CircuitStateRecord",
)
