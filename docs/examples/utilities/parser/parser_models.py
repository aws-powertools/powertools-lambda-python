from typing import List, Optional

from aws_lambda_powertools.utilities.parser import BaseModel


class OrderItem(BaseModel):
    id: int
    quantity: int
    description: str


class Order(BaseModel):
    id: int
    description: str
    items: List[OrderItem]  # nesting models are supported
    optional_field: Optional[str]  # this field may or may not be available when parsing
