import json
from uuid import uuid4

import requests

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")

# Treat everything under the "body" key
# in the event json object as our payload
config = IdempotencyConfig(event_key_jmespath="powertools_json(body)")


class PaymentError(Exception):
    ...


@idempotent(config=config, persistence_store=persistence_layer)
def handler(event, context) -> dict:
    body = json.loads(event["body"])
    try:
        payment: dict = create_subscription_payment(user=body["user"], product_id=body["product_id"])
        return {"payment_id": payment.get("id"), "message": "success", "statusCode": 200}
    except requests.HTTPError as e:
        raise PaymentError("Unable to create payment subscription") from e


def create_subscription_payment(user: str, product_id: str) -> dict:
    payload = {"user": user, "product_id": product_id}
    ret: requests.Response = requests.post(url="https://httpbin.org/anything", data=payload)
    ret.raise_for_status()

    return {"id": f"{uuid4()}", "message": "paid"}
