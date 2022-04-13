from typing import List, Optional

from aws_lambda_powertools.utilities.parser import BaseModel, parse
from aws_lambda_powertools.utilities.parser.models import EventBridgeModel


class OrderItem(BaseModel):
    id: int
    quantity: int
    description: str


class Order(BaseModel):
    id: int
    description: str
    items: List[OrderItem]


class OrderEventModel(EventBridgeModel):
    detail: Order


payload = {
    "version": "0",
    "id": "6a7e8feb-b491-4cf7-a9f1-bf3703467718",
    "detail-type": "OrderPurchased",
    "source": "OrderService",
    "account": "111122223333",
    "time": "2020-10-22T18:43:48Z",
    "region": "us-west-1",
    "resources": ["some_additional"],
    "detail": {
        "id": 10876546789,
        "description": "My order",
        "items": [
            {
                "id": 1015938732,
                "quantity": 1,
                "description": "item xpto",
            },
        ],
    },
}

ret = parse(model=OrderEventModel, event=payload)

assert ret.source == "OrderService"
assert ret.detail.description == "My order"
assert ret.detail_type == "OrderPurchased"  # we rename it to snake_case since detail-type is an invalid name

for order_item in ret.detail.items:
    ...
