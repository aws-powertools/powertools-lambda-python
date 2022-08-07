import json
from dataclasses import asdict, dataclass, is_dataclass
from uuid import uuid4

import powertools_json_jmespath_schema as schemas
from jmespath.exceptions import JMESPathTypeError

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import SchemaValidationError, validate


@dataclass
class Order:
    order_id: str
    user_id: int
    product_id: int
    quantity: int
    price: float
    currency: str


class DataclassCustomEncoder(json.JSONEncoder):
    """A custom JSON encoder to serialize dataclass obj"""

    def default(self, obj):
        # Only called for values that aren't JSON serializable
        # where `obj` will be an instance of Todo in this example
        return asdict(obj) if is_dataclass(obj) else super().default(obj)


def lambda_handler(event, context: LambdaContext) -> dict:

    # Let's validate the schema
    try:
        validate(event=event, schema=schemas.INPUT, envelope="powertools_json(payload)")

        order = create_order(json.loads(event["payload"]))
        return {
            "order": json.dumps(order.get("order"), cls=DataclassCustomEncoder),
            "message": order.get("message"),
            "success": True,
        }
    except JMESPathTypeError:
        return return_error_message("The powertools_json() envelope function must match a valid path.")
    except json.JSONDecodeError:
        return return_error_message("Payload must be valid JSON (base64 encoded).")
    except SchemaValidationError as exception:

        # if validation fails, a SchemaValidationError will be raised with the wrong fields
        return return_error_message(str(exception))


def create_order(event: dict) -> dict:
    # This return an Order dataclass
    order_id = str(uuid4())
    order = Order(
        order_id=order_id,
        user_id=event.get("user_id"),
        product_id=event.get("product_id"),
        quantity=event.get("quantity"),
        price=event.get("price"),
        currency=event.get("currency"),
    )
    return {"order": order, "message": "order created"}


def return_error_message(message: str) -> dict:
    return {"order": None, "message": message, "success": False}
