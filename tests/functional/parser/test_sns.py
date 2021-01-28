from typing import Any, List

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyAdvancedSnsBusiness, MySnsBusiness
from tests.functional.parser.utils import load_event
from tests.functional.validator.conftest import sns_event  # noqa: F401


@event_parser(model=MySnsBusiness, envelope=envelopes.SnsEnvelope)
def handle_sns_json_body(event: List[MySnsBusiness], _: LambdaContext):
    assert len(event) == 1
    assert event[0].message == "hello world"
    assert event[0].username == "lessa"


def test_handle_sns_trigger_event_json_body(sns_event):  # noqa: F811
    handle_sns_json_body(sns_event, LambdaContext())


def test_validate_event_does_not_conform_with_model():
    event: Any = {"invalid": "event"}

    with pytest.raises(ValidationError):
        handle_sns_json_body(event, LambdaContext())


def test_validate_event_does_not_conform_user_json_string_with_model():
    event: Any = {
        "Records": [
            {
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-2:123456789012:sns-la ...",
                "EventSource": "aws:sns",
                "Sns": {
                    "SignatureVersion": "1",
                    "Timestamp": "2019-01-02T12:45:07.000Z",
                    "Signature": "tcc6faL2yUC6dgZdmrwh1Y4cGa/ebXEkAi6RibDsvpi+tE/1+82j...65r==",
                    "SigningCertUrl": "https://sns.us-east-2.amazonaws.com/SimpleNotificat ...",
                    "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                    "Message": "not a valid JSON!",
                    "MessageAttributes": {"Test": {"Type": "String", "Value": "TestString"}},
                    "Type": "Notification",
                    "UnsubscribeUrl": "https://sns.us-east-2.amazonaws.com/?Action=Unsubscri ...",
                    "TopicArn": "arn:aws:sns:us-east-2:123456789012:sns-lambda",
                    "Subject": "TestInvoke",
                },
            }
        ]
    }

    with pytest.raises(ValidationError):
        handle_sns_json_body(event, LambdaContext())


@event_parser(model=MyAdvancedSnsBusiness)
def handle_sns_no_envelope(event: MyAdvancedSnsBusiness, _: LambdaContext):
    records = event.Records
    record = records[0]

    assert len(records) == 1
    assert record.EventVersion == "1.0"
    assert record.EventSubscriptionArn == "arn:aws:sns:us-east-2:123456789012:sns-la ..."
    assert record.EventSource == "aws:sns"
    assert record.Sns.Type == "Notification"
    assert record.Sns.UnsubscribeUrl.scheme == "https"
    assert record.Sns.UnsubscribeUrl.host == "sns.us-east-2.amazonaws.com"
    assert record.Sns.UnsubscribeUrl.query == "Action=Unsubscribe"
    assert record.Sns.TopicArn == "arn:aws:sns:us-east-2:123456789012:sns-lambda"
    assert record.Sns.Subject == "TestInvoke"
    assert record.Sns.SignatureVersion == "1"
    convert_time = int(round(record.Sns.Timestamp.timestamp() * 1000))
    assert convert_time == 1546433107000
    assert record.Sns.Signature == "tcc6faL2yUC6dgZdmrwh1Y4cGa/ebXEkAi6RibDsvpi+tE/1+82j...65r=="
    assert record.Sns.SigningCertUrl.host == "sns.us-east-2.amazonaws.com"
    assert record.Sns.SigningCertUrl.scheme == "https"
    assert record.Sns.SigningCertUrl.host == "sns.us-east-2.amazonaws.com"
    assert record.Sns.SigningCertUrl.path == "/SimpleNotification"
    assert record.Sns.MessageId == "95df01b4-ee98-5cb9-9903-4c221d41eb5e"
    assert record.Sns.Message == "Hello from SNS!"
    attrib_dict = record.Sns.MessageAttributes
    assert len(attrib_dict) == 2
    assert attrib_dict["Test"].Type == "String"
    assert attrib_dict["Test"].Value == "TestString"
    assert attrib_dict["TestBinary"].Type == "Binary"
    assert attrib_dict["TestBinary"].Value == "TestBinary"


def test_handle_sns_trigger_event_no_envelope():
    event_dict = load_event("snsEvent.json")
    handle_sns_no_envelope(event_dict, LambdaContext())


@event_parser(model=MySnsBusiness, envelope=envelopes.SnsSqsEnvelope)
def handle_sns_sqs_json_body(event: List[MySnsBusiness], _: LambdaContext):
    assert len(event) == 1
    assert event[0].message == "hello world"
    assert event[0].username == "lessa"


def test_handle_sns_sqs_trigger_event_json_body():  # noqa: F811
    event_dict = load_event("snsSqsEvent.json")
    handle_sns_sqs_json_body(event_dict, LambdaContext())
