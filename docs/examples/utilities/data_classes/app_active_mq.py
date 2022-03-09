from typing import Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.active_mq_event import ActiveMQEvent

logger = Logger()


@event_source(data_class=ActiveMQEvent)
def lambda_handler(event: ActiveMQEvent, context):
    for message in event.messages:
        logger.debug(f"MessageID: {message.message_id}")
        data: Dict = message.json_data
        logger.debug("Process json in base64 encoded data str", data)
