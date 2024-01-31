import base64
import binascii
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from uuid import uuid4

import powertools_base64_jmespath_schema as schemas
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
        # where `obj` will be an instance of Todo in this example
        return asdict(obj) if is_dataclass(obj) else super().default(obj)


def lambda_handler(event, context: LambdaContext) -> dict:
    # Try to validate the schema
    try:
        validate(event=event, schema=schemas.INPUT, envelope="powertools_json(powertools_base64(payload))")

        # alternatively, extract_data_from_envelope works here too
        payload_decoded = base64.b64decode(event["payload"]).decode()

        order_payload: dict = json.loads(payload_decoded)

        return {
            "order": json.dumps(Order(**order_payload), cls=DataclassCustomEncoder),
            "message": "order created",
            "success": True,
        }
    except JMESPathTypeError:
        return return_error_message(
            "The powertools_json(powertools_base64()) envelope function must match a valid path.",
        )
    except binascii.Error:
        return return_error_message("Payload must be a valid base64 encoded string")
    except json.JSONDecodeError:
        return return_error_message("Payload must be valid JSON (base64 encoded).")
    except SchemaValidationError as exception:
        # SchemaValidationError indicates where a data mismatch is
        return return_error_message(str(exception))


def return_error_message(message: str) -> dict:
    return {"order": None, "message": message, "success": False}
