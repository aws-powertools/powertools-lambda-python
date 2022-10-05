from dataclasses import dataclass, field
from typing import Callable
from uuid import uuid4

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.jmespath_utils import (
    envelopes,
    extract_data_from_envelope,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


@dataclass
class Payment:
    user_id: str
    order_id: str
    amount: float
    status_id: str
    payment_id: str = field(default_factory=lambda: f"{uuid4()}")


class PaymentError(Exception):
    ...


@lambda_handler_decorator
def middleware_before(handler, event, context) -> Callable:
    # extract payload from a EventBridge event
    detail: dict = extract_data_from_envelope(data=event, envelope=envelopes.EVENTBRIDGE)

    # check if status_id exists in payload, otherwise add default state before processing payment
    if "status_id" not in detail:
        event["detail"]["status_id"] = "pending"

    response = handler(event, context)

    return response


@middleware_before
def lambda_handler(event, context: LambdaContext) -> dict:
    try:
        payment_payload: dict = extract_data_from_envelope(data=event, envelope=envelopes.EVENTBRIDGE)
        return {
            "order": Payment(**payment_payload).__dict__,
            "message": "payment created",
            "success": True,
        }
    except Exception as e:
        raise PaymentError("Unable to create payment") from e
