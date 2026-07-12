import os

from aws_lambda_powertools.utilities.circuit_breaker_alpha import circuit_breaker
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence import (
    CircuitBreakerDynamoDBPersistence,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

table = os.getenv("CIRCUIT_BREAKER_TABLE", "")
persistence = CircuitBreakerDynamoDBPersistence(
    table_name=table,
    key_attr="PK",
    sort_key_attr="SK",
    static_pk_value="CIRCUIT_BREAKER",
)


class PaymentBackend:
    def charge(self, order: dict): ...


payment_api = PaymentBackend()


@circuit_breaker(name="payment-backend", persistence_store=persistence)
def charge(order: dict) -> dict:
    return payment_api.charge(order)  # the protected downstream call


def lambda_handler(event: dict, context: LambdaContext):
    return charge(event)
