import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, parse
from tests.functional.utils import load_event
from tests.functional.validator.conftest import sqs_event  # noqa: F401
from tests.unit.parser.schemas import MyAdvancedSqsBusiness, MySqsBusiness


def test_handle_sqs_trigger_event_json_body(sqs_event):  # noqa: F811
    parsed_event: MySqsBusiness = parse(event=sqs_event, model=MySqsBusiness, envelope=envelopes.SqsEnvelope)

    assert len(parsed_event) == 1
    assert parsed_event[0].message == "hello world"
    assert parsed_event[0].username == "lessa"


def test_validate_event_does_not_conform_with_model():
    raw_event: dict = {"invalid": "event"}

    with pytest.raises(ValidationError):
        parse(event=raw_event, model=MySqsBusiness, envelope=envelopes.SqsEnvelope)


def test_validate_event_does_not_conform_user_json_string_with_model():
    raw_event: dict = {
        "Records": [
            {
                "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
                "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a...",
                "body": "Not valid json",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1545082649183",
                    "SenderId": "AIDAIENQZJOLO23YVJ4VO",
                    "ApproximateFirstReceiveTimestamp": "1545082649185",
                },
                "messageAttributes": {
                    "testAttr": {"stringValue": "100", "binaryValue": "base64Str", "dataType": "Number"},
                },
                "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-2:123456789012:my-queue",
                "awsRegion": "us-east-2",
            },
        ],
    }

    with pytest.raises(ValidationError):
        parse(event=raw_event, model=MySqsBusiness, envelope=envelopes.SqsEnvelope)


def test_handle_sqs_trigger_event_no_envelope():
    raw_event = load_event("sqsEvent.json")
    parsed_event: MyAdvancedSqsBusiness = MyAdvancedSqsBusiness(**raw_event)

    records = parsed_event.Records
    record = records[0]
    raw_record = raw_event["Records"][0]
    assert len(records) == 2

    assert record.messageId == raw_record["messageId"]
    assert record.receiptHandle == raw_record["receiptHandle"]
    assert record.body == raw_record["body"]
    assert record.eventSource == raw_record["eventSource"]
    assert record.eventSourceARN == raw_record["eventSourceARN"]
    assert record.awsRegion == raw_record["awsRegion"]
    assert record.md5OfBody == raw_record["md5OfBody"]

    attributes = record.attributes
    assert attributes.AWSTraceHeader is None
    assert attributes.ApproximateReceiveCount == raw_record["attributes"]["ApproximateReceiveCount"]
    assert attributes.SequenceNumber is None
    assert attributes.MessageGroupId is None
    assert attributes.MessageDeduplicationId is None
    assert attributes.SenderId == raw_record["attributes"]["SenderId"]
    convert_time = int(round(attributes.ApproximateFirstReceiveTimestamp.timestamp() * 1000))
    assert convert_time == int(raw_record["attributes"]["ApproximateFirstReceiveTimestamp"])
    convert_time = int(round(attributes.SentTimestamp.timestamp() * 1000))
    assert convert_time == int(raw_record["attributes"]["SentTimestamp"])

    message_attributes = record.messageAttributes
    message_attributes_raw = raw_record["messageAttributes"]["testAttr"]
    test_attr = message_attributes["testAttr"]
    assert message_attributes.get("NotFound") is None
    assert test_attr.stringValue == message_attributes_raw["stringValue"]
    assert test_attr.binaryValue == message_attributes_raw["binaryValue"]
    assert test_attr.dataType == message_attributes_raw["dataType"]
