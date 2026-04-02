from __future__ import annotations

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app: APIGatewayRestResolver = APIGatewayRestResolver(enable_validation=True)


class Product(BaseModel):
    id: int
    name: str
    price: float


@app.get("/products")
def get_products() -> list[Product]:
    return [
        Product(id=1, name="Widget", price=9.99),
    ]


def handler(event, context):
    return app.resolve(event, context)
