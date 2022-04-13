import schemas

from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError


def handler(event, context):
    try:
        validate(event=event, schema=schemas.INPUT)
    except SchemaValidationError as e:
        # do something before re-raising
        raise

    return event
