import schemas

from aws_lambda_powertools.utilities.validation import envelopes, validator


@validator(inbound_schema=schemas.INPUT, envelope=envelopes.EVENTBRIDGE)
def handler(event, context):
    return event
