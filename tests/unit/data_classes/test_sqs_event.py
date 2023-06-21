from aws_lambda_powertools.utilities.data_classes import SQSEvent
from tests.functional.utils import load_event


def test_seq_trigger_event():
    raw_event = load_event("sqsEvent.json")
    parsed_event = SQSEvent(raw_event)

    records = list(parsed_event.records)
    record = records[0]
    attributes = record.attributes
    message_attributes = record.message_attributes
    test_attr = message_attributes["testAttr"]

    assert len(records) == 2
    assert record.message_id == raw_event["Records"][0]["messageId"]
    assert record.receipt_handle == raw_event["Records"][0]["receiptHandle"]
    assert record.body == raw_event["Records"][0]["body"]
    assert attributes.aws_trace_header is None
    assert attributes.approximate_receive_count == raw_event["Records"][0]["attributes"]["ApproximateReceiveCount"]
    assert attributes.sent_timestamp == raw_event["Records"][0]["attributes"]["SentTimestamp"]
    assert attributes.sender_id == raw_event["Records"][0]["attributes"]["SenderId"]
    assert (
        attributes.approximate_first_receive_timestamp
        == raw_event["Records"][0]["attributes"]["ApproximateFirstReceiveTimestamp"]
    )
    assert attributes.sequence_number is None
    assert attributes.message_group_id is None
    assert attributes.message_deduplication_id is None
    assert message_attributes["NotFound"] is None
    assert message_attributes.get("NotFound") is None
    assert test_attr.string_value == raw_event["Records"][0]["messageAttributes"]["testAttr"]["stringValue"]
    assert test_attr.binary_value == raw_event["Records"][0]["messageAttributes"]["testAttr"]["binaryValue"]
    assert test_attr.data_type == raw_event["Records"][0]["messageAttributes"]["testAttr"]["dataType"]
    assert record.md5_of_body == raw_event["Records"][0]["md5OfBody"]
    assert record.event_source == raw_event["Records"][0]["eventSource"]
    assert record.event_source_arn == raw_event["Records"][0]["eventSourceARN"]
    assert record.queue_url == "https://sqs.us-east-2.amazonaws.com/123456789012/my-queue"
    assert record.aws_region == raw_event["Records"][0]["awsRegion"]

    record_2 = records[1]
    assert record_2.json_body == {"message": "foo1"}
