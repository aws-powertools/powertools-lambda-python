from typing import Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.rabbit_mq_event import RabbitMQEvent

logger = Logger()


@event_source(data_class=RabbitMQEvent)
def lambda_handler(event: RabbitMQEvent, context):
    for queue_name, messages in event.rmq_messages_by_queue.items():
        logger.debug(f"Messages for queue: {queue_name}")
        for message in messages:
            logger.debug(f"MessageID: {message.basic_properties.message_id}")
            data: Dict = message.json_data
            logger.debug("Process json in base64 encoded data str", data)
