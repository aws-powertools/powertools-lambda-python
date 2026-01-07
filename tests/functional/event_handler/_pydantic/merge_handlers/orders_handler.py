from __future__ import annotations

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver(enable_validation=True)


class Order(BaseModel):
    id: int
    user_id: int
    total: float


@app.get("/orders")
def get_orders() -> list[Order]:
    return []


@app.get("/orders/<order_id>")
def get_order(order_id: int) -> Order:
    return Order(id=order_id, user_id=1, total=99.99)


def handler(event, context):
    return app.resolve(event, context)
