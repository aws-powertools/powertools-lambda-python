from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import (
    AWSConfigRuleEvent,
    event_source,
)

logger = Logger()


@event_source(data_class=AWSConfigRuleEvent)
def lambda_handler(event: AWSConfigRuleEvent, context):
    message_type = event.invoking_event.message_type

    logger.info(f"Logging {message_type} event rule", invoke_event=event.raw_invoking_event)

    return {"Success": "OK"}
