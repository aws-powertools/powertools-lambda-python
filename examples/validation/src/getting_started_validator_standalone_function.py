import getting_started_validator_standalone_schema as schemas

from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError


def lambda_handler(event, context) -> dict:
    try:
        user_authenticated: str = ""

        # using standalone function to validate input data only
        validate(event=event, schema=schemas.INPUT)

        if event.get("username") == "lambda" and event.get("password") == "powertools":
            user_authenticated = "Authenticated"

        # in this example the body can be a string because we are not validating the OUTPUT
        return {"body": user_authenticated, "statusCode": 200 if user_authenticated else 204}
    except SchemaValidationError as exception:
        # SchemaValidationError indicates where a data mismatch is
        return {"body": str(exception), "statusCode": 400}
