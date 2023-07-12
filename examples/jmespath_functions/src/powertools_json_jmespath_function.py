import json
from dataclasses import asdict, dataclass, field, is_dataclass
from uuid import uuid4

import powertools_json_jmespath_schema as schemas
from jmespath.exceptions import JMESPathTypeError

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import SchemaValidationError, validate


@dataclass
class Order:
    user_id: int
    product_id: int
    quantity: int
    price: float
    currency: str
    order_id: str = field(default_factory=lambda: f"{uuid4()}")


class DataclassCustomEncoder(json.JSONEncoder):
    """A custom JSON encoder to serialize dataclass obj"""

    def default(self, obj):
        # Only called for values that aren't JSON serializable
        # where `obj` will be an instance of Order in this example
        return asdict(obj) if is_dataclass(obj) else super().default(obj)


def lambda_handler(event, context: LambdaContext) -> dict:
    try:
        # Validate order against our schema
        validate(event=event, schema=schemas.INPUT, envelope="powertools_json(payload)")

        # Deserialize JSON string order as dict
        # alternatively, extract_data_from_envelope works here too
        order_payload: dict = json.loads(event.get("payload"))

        return {
            "order": json.dumps(Order(**order_payload), cls=DataclassCustomEncoder),
            "message": "order created",
            "success": True,
        }
    except JMESPathTypeError:
        # The powertools_json() envelope function must match a valid path
        return return_error_message("Invalid request.")
    except SchemaValidationError as exception:
        # SchemaValidationError indicates where a data mismatch is
        return return_error_message(str(exception))
    except json.JSONDecodeError:
        return return_error_message("Payload must be valid JSON (base64 encoded).")


def return_error_message(message: str) -> dict:
    return {"order": None, "message": message, "success": False}
