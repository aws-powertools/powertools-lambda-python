from custom_handlers_schema import CHILD_SCHEMA, PARENT_SCHEMA

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import validator


def get_child_schema(uri: str):
    return CHILD_SCHEMA


@validator(inbound_schema=PARENT_SCHEMA, inbound_handlers={"https": get_child_schema})
def lambda_handler(event, context: LambdaContext) -> dict:
    return event
