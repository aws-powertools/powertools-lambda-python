from aws_lambda_powertools.utilities.data_classes.active_mq_event import ActiveMQEvent, ActiveMQMessage
from tests.functional.utils import load_event


def test_activate_mq_event():
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
