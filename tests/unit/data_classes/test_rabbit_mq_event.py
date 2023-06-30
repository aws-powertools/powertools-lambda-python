from typing import Dict

from aws_lambda_powertools.utilities.data_classes.rabbit_mq_event import (
    BasicProperties,
    RabbitMessage,
    RabbitMQEvent,
)
from tests.functional.utils import load_event


def test_rabbit_mq_event():
    raw_event = load_event("rabbitMQEvent.json")
    parsed_event = RabbitMQEvent(raw_event)

    assert parsed_event.event_source == raw_event["eventSource"]
    assert parsed_event.event_source_arn == raw_event["eventSourceArn"]

    message = parsed_event.rmq_messages_by_queue["pizzaQueue::/"][0]
    assert message.redelivered is False
    assert message.data is not None
    assert message.decoded_data is not None
    assert message.json_data["timeout"] == 0
    assert message.json_data["data"] == "CZrmf0Gw8Ov4bqLQxD4E"

    assert isinstance(message, RabbitMessage)
    properties = message.basic_properties
    assert isinstance(properties, BasicProperties)
    assert (
        properties.content_type == raw_event["rmqMessagesByQueue"]["pizzaQueue::/"][0]["basicProperties"]["contentType"]
    )
    assert properties.content_encoding is None
    assert isinstance(properties.headers, Dict)
    assert properties.headers.get("header1") is not None
    assert (
        properties.delivery_mode
        == raw_event["rmqMessagesByQueue"]["pizzaQueue::/"][0]["basicProperties"]["deliveryMode"]
    )
    assert properties.priority == raw_event["rmqMessagesByQueue"]["pizzaQueue::/"][0]["basicProperties"]["priority"]
    assert properties.correlation_id is None
    assert properties.reply_to is None
    assert properties.expiration == raw_event["rmqMessagesByQueue"]["pizzaQueue::/"][0]["basicProperties"]["expiration"]
    assert properties.message_id is None
    assert properties.timestamp == raw_event["rmqMessagesByQueue"]["pizzaQueue::/"][0]["basicProperties"]["timestamp"]
    assert properties.get_type is None
    assert properties.user_id == raw_event["rmqMessagesByQueue"]["pizzaQueue::/"][0]["basicProperties"]["userId"]
    assert properties.app_id is None
    assert properties.cluster_id is None
    assert properties.body_size == raw_event["rmqMessagesByQueue"]["pizzaQueue::/"][0]["basicProperties"]["bodySize"]
