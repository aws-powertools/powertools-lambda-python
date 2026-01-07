"""
Example: Orders Lambda Handler (for OpenAPI Merge)

This is an example of a micro-function Lambda that would be discovered
by configure_openapi_merge.
"""

from __future__ import annotations

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver(enable_validation=True)


class OrderItem(BaseModel):
    product_id: int
    quantity: int
    price: float


class Order(BaseModel):
    id: int
    user_id: int
    items: list[OrderItem]
    total: float


@app.get("/orders")
def get_orders() -> list[Order]:
    """Get all orders."""
    return []


@app.get("/orders/<order_id>")
def get_order(order_id: int) -> Order:
    """Get a specific order by ID."""
    return Order(
        id=order_id,
        user_id=1,
        items=[OrderItem(product_id=1, quantity=2, price=29.99)],
        total=59.98,
    )


@app.post("/orders")
def create_order(order: Order) -> Order:
    """Create a new order."""
    return order


def handler(event, context):
    return app.resolve(event, context)
