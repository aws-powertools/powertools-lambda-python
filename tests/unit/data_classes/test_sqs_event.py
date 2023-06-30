import json

from aws_lambda_powertools.utilities.data_classes import S3Event, SQSEvent
from aws_lambda_powertools.utilities.data_classes.sns_event import SNSMessage
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
    raw_attributes = raw_event["Records"][0]["attributes"]
    assert attributes.approximate_receive_count == raw_attributes["ApproximateReceiveCount"]
    assert attributes.sent_timestamp == raw_attributes["SentTimestamp"]
    assert attributes.sender_id == raw_attributes["SenderId"]
    assert attributes.approximate_first_receive_timestamp == raw_attributes["ApproximateFirstReceiveTimestamp"]
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


def test_decode_nested_s3_event(raw_event):
    raw_event = load_event("s3SqsEvent.json")
    event = SQSEvent(raw_event)

    records = list(event.records)
    record = records[0]
    attributes = record.attributes

    assert len(records) == 1
    assert record.message_id == "ca3e7a89-c358-40e5-8aa0-5da01403c267"
    assert attributes.aws_trace_header is None
    assert attributes.approximate_receive_count == "1"
    assert attributes.sent_timestamp == "1681332219270"
    assert attributes.sender_id == "AIDAJHIPRHEMV73VRJEBU"
    assert attributes.approximate_first_receive_timestamp == "1681332239270"
    assert attributes.sequence_number is None
    assert attributes.message_group_id is None
    assert attributes.message_deduplication_id is None
    assert record.md5_of_body == "16f4460f4477d8d693a5abe94fdbbd73"
    assert record.event_source == "aws:sqs"
    assert record.event_source_arn == "arn:aws:sqs:us-east-1:123456789012:SQS"
    assert record.aws_region == "us-east-1"

    s3_event: S3Event = record.decode_nested_s3_event
    s3_record = s3_event.record

    assert s3_event.bucket_name == "xxx"
    assert s3_event.object_key == "test.pdf"
    assert s3_record.aws_region == "us-east-1"
    assert s3_record.event_name == "ObjectCreated:Put"
    assert s3_record.event_source == "aws:s3"
    assert s3_record.event_time == "2023-04-12T20:43:38.021Z"
    assert s3_record.event_version == "2.1"
    assert s3_record.glacier_event_data is None
    assert s3_record.request_parameters.source_ip_address == "93.108.161.96"
    assert s3_record.response_elements["x-amz-request-id"] == "YMSSR8BZJ2Y99K6P"
    assert s3_record.s3.s3_schema_version == "1.0"
    assert s3_record.s3.bucket.arn == "arn:aws:s3:::xxx"
    assert s3_record.s3.bucket.name == "xxx"
    assert s3_record.s3.bucket.owner_identity.principal_id == "A1YQ72UWCM96UF"
    assert s3_record.s3.configuration_id == "SNS"
    assert s3_record.s3.get_object.etag == "2e3ad1e983318bbd8e73b080e2997980"
    assert s3_record.s3.get_object.key == "test.pdf"
    assert s3_record.s3.get_object.sequencer == "00643717F9F8B85354"
    assert s3_record.s3.get_object.size == 104681
    assert s3_record.s3.get_object.version_id == "yd3d4HaWOT2zguDLvIQLU6ptDTwKBnQV"
    assert s3_record.user_identity.principal_id == "A1YQ72UWCM96UF"


def test_decode_nested_sns_event(raw_event):
    raw_event = load_event("snsSqsEvent.json")
    event = SQSEvent(raw_event)

    records = list(event.records)
    record = records[0]
    attributes = record.attributes

    assert len(records) == 1
    assert record.message_id == "79406a00-bf15-46ca-978c-22c3613fcb30"
    assert attributes.aws_trace_header is None
    assert attributes.approximate_receive_count == "1"
    assert attributes.sent_timestamp == "1611050827340"
    assert attributes.sender_id == "AIDAISMY7JYY5F7RTT6AO"
    assert attributes.approximate_first_receive_timestamp == "1611050827344"
    assert attributes.sequence_number is None
    assert attributes.message_group_id is None
    assert attributes.message_deduplication_id is None
    assert record.md5_of_body == "8910bdaaf9a30a607f7891037d4af0b0"
    assert record.event_source == "aws:sqs"
    assert record.event_source_arn == "arn:aws:sqs:eu-west-1:231436140809:powertools265"
    assert record.aws_region == "eu-west-1"

    sns_message: SNSMessage = record.decode_nested_sns_event
    message = json.loads(sns_message.message)

    assert sns_message.get_type == "Notification"
    assert sns_message.message_id == "d88d4479-6ec0-54fe-b63f-1cf9df4bb16e"
    assert sns_message.topic_arn == "arn:aws:sns:eu-west-1:231436140809:powertools265"
    assert sns_message.timestamp == "2021-01-19T10:07:07.287Z"
    assert sns_message.signature_version == "1"
    assert message["message"] == "hello world"
    assert message["username"] == "lessa"
