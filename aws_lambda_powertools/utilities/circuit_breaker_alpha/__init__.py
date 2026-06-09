"""
Circuit Breaker utility for protecting unhealthy downstream dependencies.

!!! warning "Alpha / experimental"
    This utility is published under the `_alpha` namespace while we collect
    feedback. The public API may change in a backwards-incompatible way before it
    is promoted to GA. Pin your version and follow the tracking discussion before
    relying on it in production.
"""

from aws_lambda_powertools.utilities.circuit_breaker_alpha.circuit_breaker import circuit_breaker
from aws_lambda_powertools.utilities.circuit_breaker_alpha.config import CircuitBreakerConfig
from aws_lambda_powertools.utilities.circuit_breaker_alpha.exceptions import (
    CircuitBreakerConfigError,
    CircuitBreakerError,
    CircuitBreakerOpenError,
    CircuitBreakerPersistenceError,
)
from aws_lambda_powertools.utilities.circuit_breaker_alpha.states import (
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
