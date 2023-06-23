from dataclasses import dataclass, field
from uuid import uuid4

import getting_started_validator_decorator_schema as schemas

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import validator

# we can get list of allowed IPs from AWS Parameter Store using Parameters Utility
# See: https://docs.powertools.aws.dev/lambda/python/latest/utilities/parameters/
ALLOWED_IPS = parameters.get_parameter("/lambda-powertools/allowed_ips")


class UserPermissionsError(Exception):
    ...


@dataclass
class User:
    ip: str
    permissions: list
    user_id: str = field(default_factory=lambda: f"{uuid4()}")
    name: str = "Project Lambda Powertools"


# using a decorator to validate input and output data
@validator(inbound_schema=schemas.INPUT, outbound_schema=schemas.OUTPUT)
def lambda_handler(event, context: LambdaContext) -> dict:
    try:
        user_details: dict = {}

        # get permissions by user_id and project
        if (
            event.get("user_id") == "0d44b083-8206-4a3a-aa95-5d392a99be4a"
            and event.get("project") == "powertools"
            and event.get("ip") in ALLOWED_IPS
        ):
            user_details = User(ip=event.get("ip"), permissions=["read", "write"]).__dict__

        # the body must be an object because must match OUTPUT schema, otherwise it fails
        return {"body": user_details or None, "statusCode": 200 if user_details else 204}
    except Exception as e:
        raise UserPermissionsError(str(e))
