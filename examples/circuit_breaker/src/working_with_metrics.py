import os

from aws_lambda_powertools.metrics import MetricUnit, single_metric
from aws_lambda_powertools.utilities.circuit_breaker import (
    CircuitTransition,
    circuit_breaker,
)
from aws_lambda_powertools.utilities.circuit_breaker.persistence import (
    CircuitBreakerDynamoDBPersistence,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

table = os.getenv("CIRCUIT_BREAKER_TABLE", "")
persistence = CircuitBreakerDynamoDBPersistence(table_name=table)


def emit_transition_metric(transition: CircuitTransition) -> None:
    # Fires only when the circuit changes state, so this never runs on the hot path.
    with single_metric(
        namespace="MyApplication",
        name=f"Circuit_{transition.to_state}",
        unit=MetricUnit.Count,
        value=1,
    ) as metric:
        metric.add_dimension(name="circuit", value=transition.circuit_name)


class PaymentBackend:
    def charge(self, order: dict): ...


payment_api = PaymentBackend()


@circuit_breaker(
    name="payment-backend",
    persistence_store=persistence,
    on_transition=emit_transition_metric,
)
def charge(order: dict) -> dict:
    return payment_api.charge(order)


def lambda_handler(event: dict, context: LambdaContext):
    return charge(event)
