import random
from json import JSONDecodeError

import powertools_json_jmespath_schema as schemas

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import SchemaValidationError, validate


def lambda_handler(event, context: LambdaContext) -> dict:

    # Let's validate the schema
    try:
        validate(event=event, schema=schemas.INPUT, envelope="powertools_json(payload)")

        order = create_order(event["payload"])
        return {"order_id": order.get("id"), "message": order.get("message"), "statusCode": 200}
    except JSONDecodeError:
        return return_error_message("Payload must be valid JSON (plain text).")
    except SchemaValidationError as exception:

        # if validation fails, a SchemaValidationError will be raised with the wrong fields
        return return_error_message(str(exception))


def create_order(event: dict) -> dict:
    # Add your logic here. For demostration purposes, this return a random order number
    return {"id": random.randint(1, 100), "message": "order created"}


def return_error_message(message: str) -> dict:
    return {"order_id": None, "message": message, "statusCode": 400}
