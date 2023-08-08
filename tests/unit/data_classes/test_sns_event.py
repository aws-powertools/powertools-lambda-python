from aws_lambda_powertools.utilities.data_classes import SNSEvent
from tests.functional.utils import load_event


def test_sns_trigger_event():
    raw_event = load_event("snsEvent.json")
    parsed_event = SNSEvent(raw_event)

    records = list(parsed_event.records)
    assert len(records) == 1
    record = records[0]
    assert record.event_version == raw_event["Records"][0]["EventVersion"]
    assert record.event_subscription_arn == raw_event["Records"][0]["EventSubscriptionArn"]
    assert record.event_source == raw_event["Records"][0]["EventSource"]
    sns = record.sns
    assert sns.signature_version == raw_event["Records"][0]["Sns"]["SignatureVersion"]
    assert sns.timestamp == raw_event["Records"][0]["Sns"]["Timestamp"]
    assert sns.signature == raw_event["Records"][0]["Sns"]["Signature"]
    assert sns.signing_cert_url == raw_event["Records"][0]["Sns"]["SigningCertUrl"]
    assert sns.message_id == raw_event["Records"][0]["Sns"]["MessageId"]
    assert sns.message == raw_event["Records"][0]["Sns"]["Message"]
    message_attributes = sns.message_attributes
    test_message_attribute = message_attributes["Test"]
    assert test_message_attribute.get_type == raw_event["Records"][0]["Sns"]["MessageAttributes"]["Test"]["Type"]
    assert test_message_attribute.value == raw_event["Records"][0]["Sns"]["MessageAttributes"]["Test"]["Value"]
    assert sns.get_type == raw_event["Records"][0]["Sns"]["Type"]
    assert sns.unsubscribe_url == raw_event["Records"][0]["Sns"]["UnsubscribeUrl"]
    assert sns.topic_arn == raw_event["Records"][0]["Sns"]["TopicArn"]
    assert sns.subject == raw_event["Records"][0]["Sns"]["Subject"]
    assert parsed_event.record.raw_event == raw_event["Records"][0]
    assert parsed_event.sns_message == raw_event["Records"][0]["Sns"]["Message"]
