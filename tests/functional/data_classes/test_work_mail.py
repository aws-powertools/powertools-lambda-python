from aws_lambda_powertools.utilities.data_classes.work_mail import WorkMailEvent
from tests.functional.utils import load_event


def test_work_mail():
    event = WorkMailEvent(load_event("workMailEvent.json"))

    assert event.summary_version == event["summaryVersion"]
    envelope = event.envelope
    assert envelope.mail_from == "from@example.com"
    assert envelope.recipients == ["recipient1@example.com", "recipient2@example.com"]
    assert event.sender == "sender@example.com"
    assert event.subject == event["subject"]
    assert event.message_id == event["messageId"]
    assert event.invocation_id == event["invocationId"]
    assert event.flow_direction == event["flowDirection"]
    assert event.truncated is False


def test_work_mail_sender_is_none():
    # GIVEN an event with a missing 'sender'
    event = WorkMailEvent({})
    # WHEN getting the 'sender'
    # THEN return None (and not raise a key error)
    assert event.sender is None
