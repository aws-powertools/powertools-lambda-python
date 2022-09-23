import json

from pydantic import BaseModel, validator

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventV2Model
from aws_lambda_powertools.utilities.typing import LambdaContext


class CancelOrder(BaseModel):
    order_id: int
    reason: str


class CancelOrderModel(APIGatewayProxyEventV2Model):
    body: CancelOrder  # type: ignore[assignment]

    @validator("body", pre=True)
    def transform_body_to_dict(cls, value: str):
        return json.loads(value)


@event_parser(model=CancelOrderModel)
def handler(event: CancelOrderModel, context: LambdaContext):
    cancel_order: CancelOrder = event.body

    assert cancel_order.order_id is not None
