from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.parser import BaseEnvelope, BaseModel, event_parser
from aws_lambda_powertools.utilities.parser.functions import (
    _parse_and_validate_event,
    _retrieve_or_set_model_from_cache,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import validator

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import T


class CancelOrder(BaseModel):
    order_id: int
    reason: str


class CancelOrderModel(BaseModel):
    body: CancelOrder

    @validator("body", pre=True)
    def transform_body_to_dict(cls, value):
        return json.loads(value) if isinstance(value, str) else value


class CustomEnvelope(BaseEnvelope):
    def parse(self, data: dict[str, Any] | Any | None, model: type[T]):
        adapter = _retrieve_or_set_model_from_cache(model=model)
        return _parse_and_validate_event(data=data, adapter=adapter)


@event_parser(model=CancelOrderModel, envelope=CustomEnvelope)
def lambda_handler(event: CancelOrderModel, context: LambdaContext):
    cancel_order: CancelOrder = event.body

    assert cancel_order.order_id is not None

    # Process the cancel order request
    print(f"Cancelling order {cancel_order.order_id} for reason: {cancel_order.reason}")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Order {cancel_order.order_id} cancelled successfully"}),
    }
