import json
import os

import boto3

from aws_lambda_powertools.utilities.circuit_breaker_alpha import CircuitInfo, circuit_breaker
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence import (
    CircuitBreakerDynamoDBPersistence,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

table = os.getenv("CIRCUIT_BREAKER_TABLE", "")
queue_url = os.getenv("OVERFLOW_QUEUE_URL", "")
persistence = CircuitBreakerDynamoDBPersistence(table_name=table)
sqs = boto3.client("sqs")


class PaymentBackend:
    def charge(self, order: dict) -> dict: ...


payment_api = PaymentBackend()


def buffer_payload(order: dict, circuit: CircuitInfo) -> dict:
    # Circuit is OPEN. The protected call never ran and the payload is yours to handle:
    # buffer it, drop it, or return a cached value. Here we push it to an overflow queue.
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(order))
    return {"statusCode": 202, "circuit": circuit.name}


@circuit_breaker(
    name="payment-backend",
    persistence_store=persistence,
    on_circuit_open=buffer_payload,
)
def charge(order: dict) -> dict:
    return payment_api.charge(order)


def lambda_handler(event: dict, context: LambdaContext):
    # Circuit closed -> returns the backend response.
    # Circuit open   -> buffer_payload(event, circuit) runs and its return value is returned.
    return charge(event)
