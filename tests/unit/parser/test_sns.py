import json

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, parse
from tests.functional.utils import load_event
from tests.functional.validator.conftest import sns_event  # noqa: F401
from tests.unit.parser.schemas import MyAdvancedSnsBusiness, MySnsBusiness


def test_handle_sns_trigger_event_json_body(sns_event):  # noqa: F811
    parse(event=sns_event, model=MySnsBusiness, envelope=envelopes.SnsEnvelope)


def test_validate_event_does_not_conform_with_model():
    raw_event: dict = {"invalid": "event"}

    with pytest.raises(ValidationError):
        parse(event=raw_event, model=MySnsBusiness, envelope=envelopes.SnsEnvelope)


def test_validate_event_does_not_conform_user_json_string_with_model():
    raw_event: dict = {
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
            },
        ],
    }

    with pytest.raises(ValidationError):
        parse(event=raw_event, model=MySnsBusiness, envelope=envelopes.SnsEnvelope)


def test_handle_sns_trigger_event_no_envelope():
    raw_event = load_event("snsEvent.json")
    parsed_event: MyAdvancedSnsBusiness = MyAdvancedSnsBusiness(**raw_event)

    records = parsed_event.Records
    record = records[0]
    raw_record = raw_event["Records"][0]

    assert len(records) == 1
    assert record.EventVersion == raw_record["EventVersion"]
    assert record.EventSubscriptionArn == raw_record["EventSubscriptionArn"]
    assert record.EventSource == raw_record["EventSource"]

    sns = record.Sns
    raw_sns = raw_record["Sns"]
    assert sns.Type == raw_sns["Type"]
    assert sns.UnsubscribeUrl.scheme == "https"
    assert sns.UnsubscribeUrl.host == "sns.us-east-2.amazonaws.com"
    assert sns.UnsubscribeUrl.query == "Action=Unsubscribe"
    assert sns.TopicArn == raw_sns["TopicArn"]
    assert sns.Subject == raw_sns["Subject"]
    assert sns.SignatureVersion == raw_sns["SignatureVersion"]
    convert_time = int(round(sns.Timestamp.timestamp() * 1000))
    assert convert_time == 1546433107000
    assert sns.Signature == raw_sns["Signature"]
    assert sns.SigningCertUrl.host == "sns.us-east-2.amazonaws.com"
    assert sns.SigningCertUrl.scheme == "https"
    assert sns.SigningCertUrl.host == "sns.us-east-2.amazonaws.com"
    assert sns.SigningCertUrl.path == "/SimpleNotification"
    assert sns.MessageId == raw_sns["MessageId"]
    assert sns.Message == raw_sns["Message"]

    attrib_dict = sns.MessageAttributes
    assert len(attrib_dict) == 2
    assert attrib_dict["Test"].Type == raw_sns["MessageAttributes"]["Test"]["Type"]
    assert attrib_dict["Test"].Value == raw_sns["MessageAttributes"]["Test"]["Value"]
    assert attrib_dict["TestBinary"].Type == raw_sns["MessageAttributes"]["TestBinary"]["Type"]
    assert attrib_dict["TestBinary"].Value == raw_sns["MessageAttributes"]["TestBinary"]["Value"]


def test_handle_sns_sqs_trigger_event_json_body():  # noqa: F811
    raw_event = load_event("snsSqsEvent.json")
    parsed_event: MySnsBusiness = parse(event=raw_event, model=MySnsBusiness, envelope=envelopes.SnsSqsEnvelope)

    assert len(parsed_event) == 1
    assert parsed_event[0].message == "hello world"
    assert parsed_event[0].username == "lessa"


def test_handle_sns_sqs_trigger_event_json_body_missing_unsubscribe_url():
    # GIVEN an event is tampered with a missing UnsubscribeURL
    raw_event = load_event("snsSqsEvent.json")
    payload = json.loads(raw_event["Records"][0]["body"])
    payload.pop("UnsubscribeURL")
    raw_event["Records"][0]["body"] = json.dumps(payload)

    # WHEN parsing the payload
    # THEN raise a ValidationError error
    with pytest.raises(ValidationError):
        parse(event=raw_event, model=MySnsBusiness, envelope=envelopes.SnsSqsEnvelope)


def test_handle_sns_sqs_fifo_trigger_event_json_body():
    raw_event = load_event("snsSqsFifoEvent.json")
    parsed_event: MySnsBusiness = parse(event=raw_event, model=MySnsBusiness, envelope=envelopes.SnsSqsEnvelope)

    assert len(parsed_event) == 1
    assert parsed_event[0].message == "hello world"
    assert parsed_event[0].username == "lessa"
