import getting_started_validator_standalone_schema as schemas

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import SchemaValidationError, validate

# we can get list of allowed IPs from AWS Parameter Store using Parameters Utility
# See: https://awslabs.github.io/aws-lambda-powertools-python/latest/utilities/parameters/
ALLOWED_IPS = parameters.get_parameter("/lambda-powertools/allowed_ips")


def lambda_handler(event, context: LambdaContext) -> dict:
    try:
        user_authenticated: str = ""

        # using standalone function to validate input data only
        validate(event=event, schema=schemas.INPUT)

        if (
            event.get("user_id") == "0d44b083-8206-4a3a-aa95-5d392a99be4a"
            and event.get("project") == "powertools"
            and event.get("ip") in ALLOWED_IPS
        ):
            user_authenticated = "Allowed"

        # in this example the body can be of any type because we are not validating the OUTPUT
        return {"body": user_authenticated, "statusCode": 200 if user_authenticated else 204}
    except SchemaValidationError as exception:
        # SchemaValidationError indicates where a data mismatch is
        return {"body": str(exception), "statusCode": 400}
