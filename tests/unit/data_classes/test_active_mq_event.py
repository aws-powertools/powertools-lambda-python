import pytest

from aws_lambda_powertools.utilities.data_classes.active_mq_event import (
    ActiveMQEvent,
    ActiveMQMessage,
)
from tests.functional.utils import load_event


def test_active_mq_event():
    raw_event = load_event("activeMQEvent.json")
    parsed_event = ActiveMQEvent(raw_event)

    assert parsed_event.event_source == raw_event["eventSource"]
    assert parsed_event.event_source_arn == raw_event["eventSourceArn"]
    assert len(list(parsed_event.messages)) == 3

    message = parsed_event.message
    assert isinstance(message, ActiveMQMessage)
    assert message.message_id == raw_event["messages"][0]["messageID"]
    assert message.message_type == raw_event["messages"][0]["messageType"]
    assert message.data == raw_event["messages"][0]["data"]
    assert message.decoded_data == "ABC:AAAA"
    assert message.connection_id == raw_event["messages"][0]["connectionId"]
    assert message.redelivered is False
    assert message.timestamp == raw_event["messages"][0]["timestamp"]
    assert message.broker_in_time == raw_event["messages"][0]["brokerInTime"]
    assert message.broker_out_time == raw_event["messages"][0]["brokerOutTime"]
    assert message.properties.get("testKey") == raw_event["messages"][0]["properties"]["testKey"]
    assert message.destination_physicalname == raw_event["messages"][0]["destination"]["physicalname"]
    assert message.delivery_mode is None
    assert message.correlation_id is None
    assert message.reply_to is None
    assert message.get_type is None
    assert message.expiration is None
    assert message.priority is None

    messages = list(parsed_event.messages)
    message = messages[1]
    assert message.json_data["timeout"] == 0
    assert message.json_data["data"] == "CZrmf0Gw8Ov4bqLQxD4E"

    assert parsed_event.message == messages[1]
    assert parsed_event.message == messages[2]


def test_activemq_message_property_with_stopiteration_error():
    # GIVEN a kafka event with one record
    raw_event = load_event("activeMQEvent.json")
    parsed_event = ActiveMQEvent(raw_event)

    # WHEN calling record property four times
    # THEN raise StopIteration
    with pytest.raises(StopIteration):
        assert parsed_event.message.message_id is not None
        assert parsed_event.message.message_type is not None
        assert parsed_event.message.data is not None
        assert parsed_event.message.decoded_data is not None
