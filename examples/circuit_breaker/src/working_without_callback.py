import os

from aws_lambda_powertools.utilities.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    circuit_breaker,
)
from aws_lambda_powertools.utilities.circuit_breaker.persistence import (
    CircuitBreakerDynamoDBPersistence,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

table = os.getenv("CIRCUIT_BREAKER_TABLE", "")
persistence = CircuitBreakerDynamoDBPersistence(table_name=table)

config = CircuitBreakerConfig(
    failure_threshold=5,  # consecutive failures before opening
    recovery_timeout=30,  # seconds in OPEN before a half-open probe
    success_threshold=3,  # consecutive probe successes before closing
    # Only these exceptions count as a failure. A ValueError (caller's fault) is
    # re-raised without affecting the circuit.
    handled_exceptions=(TimeoutError, ConnectionError),
)


class PaymentBackend:
    def charge(self, order: dict): ...


payment_api = PaymentBackend()


@circuit_breaker(name="payment-backend", persistence_store=persistence, config=config)
def charge(order: dict) -> dict:
    return payment_api.charge(order)


def lambda_handler(event: dict, context: LambdaContext):
    try:
        return charge(event)
    except CircuitBreakerOpenError as exc:
        # No callback registered, so we decide what to do with the rejected request here.
        circuit_name = exc.circuit.name if exc.circuit else "unknown"
        return {"statusCode": 202, "circuit": circuit_name}
