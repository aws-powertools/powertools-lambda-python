import json
from dataclasses import dataclass, field
from uuid import uuid4

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")

# Deserialize JSON string under the "body" key
# then extract "user" and "product_id" data
config = IdempotencyConfig(event_key_jmespath='powertools_json(body).["user_id", "product_id"]')


@dataclass
class Payment:
    user_id: str
    product_id: str
    payment_id: str = field(default_factory=lambda: f"{uuid4()}")


class PaymentError(Exception):
    ...


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext):
    try:
        payment_info: str = event.get("body", "")
        payment: Payment = create_subscription_payment(json.loads(payment_info))
        return {
            "payment_id": payment.payment_id,
            "message": "success",
            "statusCode": 200,
        }
    except Exception as exc:
        raise PaymentError(f"Error creating payment {str(exc)}")


def create_subscription_payment(event: dict) -> Payment:
    return Payment(**event)
