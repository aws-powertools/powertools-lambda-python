import schemas

from aws_lambda_powertools.utilities.validation import validator


@validator(inbound_schema=schemas.INPUT, outbound_schema=schemas.OUTPUT)
def handler(event, context):
    return event
