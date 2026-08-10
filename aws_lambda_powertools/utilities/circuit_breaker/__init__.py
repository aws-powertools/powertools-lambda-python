"""
Circuit Breaker utility for protecting unhealthy downstream dependencies.
"""

from aws_lambda_powertools.utilities.circuit_breaker.circuit_breaker import circuit_breaker
from aws_lambda_powertools.utilities.circuit_breaker.config import CircuitBreakerConfig
from aws_lambda_powertools.utilities.circuit_breaker.exceptions import (
    CircuitBreakerConfigError,
    CircuitBreakerError,
    CircuitBreakerOpenError,
    CircuitBreakerPersistenceError,
)
from aws_lambda_powertools.utilities.circuit_breaker.states import (
    CircuitInfo,
    CircuitState,
    CircuitTransition,
)

__all__ = (
    "circuit_breaker",
    "CircuitBreakerConfig",
    "CircuitInfo",
    "CircuitState",
    "CircuitTransition",
    "CircuitBreakerError",
    "CircuitBreakerOpenError",
    "CircuitBreakerConfigError",
    "CircuitBreakerPersistenceError",
)
