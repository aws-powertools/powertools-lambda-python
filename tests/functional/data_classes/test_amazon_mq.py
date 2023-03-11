from typing import Dict

from aws_lambda_powertools.utilities.data_classes.active_mq_event import (
    ActiveMQEvent,
    ActiveMQMessage,
)
from aws_lambda_powertools.utilities.data_classes.rabbit_mq_event import (
    BasicProperties,
    RabbitMessage,
    RabbitMQEvent,
)
from tests.functional.utils import load_event


def test_active_mq_event():
    event = ActiveMQEvent(load_event("activeMQEvent.json"))

    assert event.event_source == "aws:amq"
    assert event.event_source_arn is not None
    assert len(list(event.messages)) == 3

    message = event.message
    assert isinstance(message, ActiveMQMessage)
    assert message.message_id is not None
    assert message.message_type is not None
    assert message.data is not None
    assert message.decoded_data is not None
    assert message.connection_id is not None
    assert message.redelivered is False
    assert message.timestamp is not None
    assert message.broker_in_time is not None
    assert message.broker_out_time is not None
    assert message.properties["testKey"] == "testValue"
    assert message.destination_physicalname is not None
    assert message.delivery_mode is None
    assert message.correlation_id is None
    assert message.reply_to is None
    assert message.get_type is None
    assert message.expiration is None
    assert message.priority is None

    messages = list(event.messages)
    message = messages[1]
    assert message.json_data["timeout"] == 0
    assert message.json_data["data"] == "CZrmf0Gw8Ov4bqLQxD4E"


def test_rabbit_mq_event():
    event = RabbitMQEvent(load_event("rabbitMQEvent.json"))

    assert event.event_source == "aws:rmq"
    assert event.event_source_arn is not None

    message = event.rmq_messages_by_queue["pizzaQueue::/"][0]
    assert message.redelivered is False
    assert message.data is not None
    assert message.decoded_data is not None
    assert message.json_data["timeout"] == 0
    assert message.json_data["data"] == "CZrmf0Gw8Ov4bqLQxD4E"

    assert isinstance(message, RabbitMessage)
    properties = message.basic_properties
    assert isinstance(properties, BasicProperties)
    assert properties.content_type == "text/plain"
    assert properties.content_encoding is None
    assert isinstance(properties.headers, Dict)
    assert properties.headers["header1"] is not None
    assert properties.delivery_mode == 1
    assert properties.priority == 34
    assert properties.correlation_id is None
    assert properties.reply_to is None
    assert properties.expiration == "60000"
    assert properties.message_id is None
    assert properties.timestamp is not None
    assert properties.get_type is None
    assert properties.user_id is not None
    assert properties.app_id is None
    assert properties.cluster_id is None
    assert properties.body_size == 80
