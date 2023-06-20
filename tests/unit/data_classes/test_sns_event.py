from aws_lambda_powertools.utilities.data_classes import SNSEvent
from tests.functional.utils import load_event


def test_sns_trigger_event():
    event = SNSEvent(load_event("snsEvent.json"))
    records = list(event.records)
    assert len(records) == 1
    record = records[0]
    assert record.event_version == "1.0"
    assert record.event_subscription_arn == "arn:aws:sns:us-east-2:123456789012:sns-la ..."
    assert record.event_source == "aws:sns"
    sns = record.sns
    assert sns.signature_version == "1"
    assert sns.timestamp == "2019-01-02T12:45:07.000Z"
    assert sns.signature == "tcc6faL2yUC6dgZdmrwh1Y4cGa/ebXEkAi6RibDsvpi+tE/1+82j...65r=="
    assert sns.signing_cert_url == "https://sns.us-east-2.amazonaws.com/SimpleNotification"
    assert sns.message_id == "95df01b4-ee98-5cb9-9903-4c221d41eb5e"
    assert sns.message == "Hello from SNS!"
    message_attributes = sns.message_attributes
    test_message_attribute = message_attributes["Test"]
    assert test_message_attribute.get_type == "String"
    assert test_message_attribute.value == "TestString"
    assert sns.get_type == "Notification"
    assert sns.unsubscribe_url == "https://sns.us-east-2.amazonaws.com/?Action=Unsubscribe"
    assert sns.topic_arn == "arn:aws:sns:us-east-2:123456789012:sns-lambda"
    assert sns.subject == "TestInvoke"
    assert event.record.raw_event == event["Records"][0]
    assert event.sns_message == "Hello from SNS!"
