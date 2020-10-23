from typing import Any, List

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyAdvancedSqsBusiness, MySqsBusiness
from tests.functional.parser.utils import load_event
from tests.functional.validator.conftest import sqs_event  # noqa: F401


@event_parser(model=MySqsBusiness, envelope=envelopes.SqsEnvelope)
def handle_sqs_json_body(event: List[MySqsBusiness], _: LambdaContext):
    assert len(event) == 1
    assert event[0].message == "hello world"
    assert event[0].username == "lessa"


def test_handle_sqs_trigger_event_json_body(sqs_event):  # noqa: F811
    handle_sqs_json_body(sqs_event, LambdaContext())


def test_validate_event_does_not_conform_with_model():
    event: Any = {"invalid": "event"}

    with pytest.raises(ValidationError):
        handle_sqs_json_body(event, LambdaContext())


def test_validate_event_does_not_conform_user_json_string_with_model():
    event: Any = {
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
                    "testAttr": {"stringValue": "100", "binaryValue": "base64Str", "dataType": "Number"}
                },
                "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-2:123456789012:my-queue",
                "awsRegion": "us-east-2",
            }
        ]
    }

    with pytest.raises(ValidationError):
        handle_sqs_json_body(event, LambdaContext())


@event_parser(model=MyAdvancedSqsBusiness)
def handle_sqs_no_envelope(event: MyAdvancedSqsBusiness, _: LambdaContext):
    records = event.Records
    record = records[0]
    attributes = record.attributes
    message_attributes = record.messageAttributes
    test_attr = message_attributes["testAttr"]

    assert len(records) == 2
    assert record.messageId == "059f36b4-87a3-44ab-83d2-661975830a7d"
    assert record.receiptHandle == "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a..."
    assert record.body == "Test message."
    assert attributes.AWSTraceHeader is None
    assert attributes.ApproximateReceiveCount == "1"
    convert_time = int(round(attributes.SentTimestamp.timestamp() * 1000))
    assert convert_time == 1545082649183
    assert attributes.SenderId == "AIDAIENQZJOLO23YVJ4VO"
    convert_time = int(round(attributes.ApproximateFirstReceiveTimestamp.timestamp() * 1000))
    assert convert_time == 1545082649185
    assert attributes.SequenceNumber is None
    assert attributes.MessageGroupId is None
    assert attributes.MessageDeduplicationId is None
    assert message_attributes.get("NotFound") is None
    assert test_attr.stringValue == "100"
    assert test_attr.binaryValue == "base64Str"
    assert test_attr.dataType == "Number"
    assert record.md5OfBody == "e4e68fb7bd0e697a0ae8f1bb342846b3"
    assert record.eventSource == "aws:sqs"
    assert record.eventSourceARN == "arn:aws:sqs:us-east-2:123456789012:my-queue"
    assert record.awsRegion == "us-east-2"


def test_handle_sqs_trigger_event_no_envelope():
    event_dict = load_event("sqsEvent.json")
    handle_sqs_no_envelope(event_dict, LambdaContext())
