import json

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.active_mq_event import ActiveMQEvent

logger = Logger()


@event_source(data_class=ActiveMQEvent)
def lambda_handler(event: ActiveMQEvent, context):
    for message in event.messages:
        msg = message.message_id
        msg_pn = message.destination_physicalname

        logger.info(f"Message ID: {msg} and physical name: {msg_pn}")

    return {"statusCode": 200, "body": json.dumps("Processing complete")}
