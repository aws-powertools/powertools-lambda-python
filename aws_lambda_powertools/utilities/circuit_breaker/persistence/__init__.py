"""
Persistence layers for the Circuit Breaker utility.
"""

from aws_lambda_powertools.utilities.circuit_breaker.persistence.base import CircuitBreakerPersistenceLayer
from aws_lambda_powertools.utilities.circuit_breaker.persistence.dynamodb import (
    CircuitBreakerDynamoDBPersistence,
)
from aws_lambda_powertools.utilities.circuit_breaker.persistence.record import CircuitStateRecord

__all__ = (
    "CircuitBreakerPersistenceLayer",
    "CircuitBreakerDynamoDBPersistence",
    "CircuitStateRecord",
)
