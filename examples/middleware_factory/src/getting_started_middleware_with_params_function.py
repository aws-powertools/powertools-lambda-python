import base64
from dataclasses import dataclass, field
from typing import Any, Callable, List
from uuid import uuid4

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.jmespath_utils import (
    envelopes,
    extract_data_from_envelope,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


@dataclass
class Booking:
    days: int
    date_from: str
    date_to: str
    hotel_id: int
    country: str
    city: str
    guest: dict
    booking_id: str = field(default_factory=lambda: f"{uuid4()}")


class BookingError(Exception):
    ...


@lambda_handler_decorator
def obfuscate_sensitive_data(handler, event, context, fields: List) -> Callable:
    # extracting payload from a EventBridge event
    detail: dict = extract_data_from_envelope(data=event, envelope=envelopes.EVENTBRIDGE)
    guest_data: Any = detail.get("guest")

    # Obfuscate fields (email, vat, passport) before calling Lambda handler
    for guest_field in fields:
        if guest_data.get(guest_field):
            event["detail"]["guest"][guest_field] = obfuscate_data(str(guest_data.get(guest_field)))

    response = handler(event, context)

    return response


def obfuscate_data(value: str) -> bytes:
    # base64 is not effective for obfuscation, this is an example
    return base64.b64encode(value.encode("ascii"))


@obfuscate_sensitive_data(fields=["email", "passport", "vat"])
def lambda_handler(event, context: LambdaContext) -> dict:
    try:
        booking_payload: dict = extract_data_from_envelope(data=event, envelope=envelopes.EVENTBRIDGE)
        return {
            "book": Booking(**booking_payload).__dict__,
            "message": "booking created",
            "success": True,
        }
    except Exception as e:
        raise BookingError("Unable to create booking") from e
