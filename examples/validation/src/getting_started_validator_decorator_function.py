from dataclasses import dataclass, field
from uuid import uuid4

import getting_start_validator_schema as schemas

from aws_lambda_powertools.utilities.validation import validator


@dataclass
class User:
    ip: str
    permissions: list
    user_id: str = field(default_factory=lambda: f"{uuid4()}")
    name: str = "Project Lambda Powertools"


# using a decorator to validate input and output data
@validator(inbound_schema=schemas.INPUT, outbound_schema=schemas.OUTPUT)
def lambda_handler(event, context) -> dict:

    user_details: dict = {}

    if event.get("username") == "lambda" and event.get("password") == "powertools":
        user_details = User(ip=event.get("ip"), permissions=["read", "write"]).__dict__

    # the body must be a object because must match OUTPUT schema, otherwise it fails
    return {"body": user_details or None, "statusCode": 200 if user_details else 204}
