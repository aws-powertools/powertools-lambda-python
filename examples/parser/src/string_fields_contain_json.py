from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Json

from aws_lambda_powertools.utilities.parser import BaseEnvelope, event_parser
from aws_lambda_powertools.utilities.parser.functions import (
    _parse_and_validate_event,
    _retrieve_or_set_model_from_cache,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import T


class CancelOrder(BaseModel):
    order_id: int
    reason: str


class CancelOrderModel(BaseModel):
    body: Json[CancelOrder]


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
        "body": f"Order {cancel_order.order_id} cancelled successfully",
    }
