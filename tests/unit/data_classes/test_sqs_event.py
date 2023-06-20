from aws_lambda_powertools.utilities.data_classes import SQSEvent
from tests.functional.utils import load_event


def test_seq_trigger_event():
    event = SQSEvent(load_event("sqsEvent.json"))

    records = list(event.records)
    record = records[0]
    attributes = record.attributes
    message_attributes = record.message_attributes
    test_attr = message_attributes["testAttr"]

    assert len(records) == 2
    assert record.message_id == "059f36b4-87a3-44ab-83d2-661975830a7d"
    assert record.receipt_handle == "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a..."
    assert record.body == "Test message."
    assert attributes.aws_trace_header is None
    assert attributes.approximate_receive_count == "1"
    assert attributes.sent_timestamp == "1545082649183"
    assert attributes.sender_id == "AIDAIENQZJOLO23YVJ4VO"
    assert attributes.approximate_first_receive_timestamp == "1545082649185"
    assert attributes.sequence_number is None
    assert attributes.message_group_id is None
    assert attributes.message_deduplication_id is None
    assert message_attributes["NotFound"] is None
    assert message_attributes.get("NotFound") is None
    assert test_attr.string_value == "100"
    assert test_attr.binary_value == "base64Str"
    assert test_attr.data_type == "Number"
    assert record.md5_of_body == "e4e68fb7bd0e697a0ae8f1bb342846b3"
    assert record.event_source == "aws:sqs"
    assert record.event_source_arn == "arn:aws:sqs:us-east-2:123456789012:my-queue"
    assert record.queue_url == "https://sqs.us-east-2.amazonaws.com/123456789012/my-queue"
    assert record.aws_region == "us-east-2"

    record_2 = records[1]
    assert record_2.json_body == {"message": "foo1"}
