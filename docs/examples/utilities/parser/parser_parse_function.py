from typing import List, Optional

from aws_lambda_powertools.utilities.parser import BaseModel, ValidationError, parse


class OrderItem(BaseModel):
    id: int
    quantity: int
    description: str


class Order(BaseModel):
    id: int
    description: str
    items: List[OrderItem]  # nesting models are supported
    optional_field: Optional[str]  # this field may or may not be available when parsing


payload = {
    "id": 10876546789,
    "description": "My order",
    "items": [
        {
            # this will cause a validation error
            "id": [1015938732],
            "quantity": 1,
            "description": "item xpto",
        }
    ],
}


def my_function():
    try:
        parsed_payload: Order = parse(event=payload, model=Order)
        # payload dict is now parsed into our model
        return parsed_payload.items
    except ValidationError:
        return {"status_code": 400, "message": "Invalid order"}
