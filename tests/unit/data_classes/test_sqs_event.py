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


def test_decode_nested_s3_event():
    raw_event = load_event("s3SqsEvent.json")
    event = SQSEvent(raw_event)

    records = list(event.records)
    record = records[0]
    attributes = record.attributes

    assert len(records) == 1
    assert record.message_id == raw_event["Records"][0]["messageId"]
    assert attributes.aws_trace_header is None
    raw_attributes = raw_event["Records"][0]["attributes"]
    assert attributes.approximate_receive_count == raw_attributes["ApproximateReceiveCount"]
    assert attributes.sent_timestamp == raw_attributes["SentTimestamp"]
    assert attributes.sender_id == raw_attributes["SenderId"]
    assert attributes.approximate_first_receive_timestamp == raw_attributes["ApproximateFirstReceiveTimestamp"]
    assert attributes.sequence_number is None
    assert attributes.message_group_id is None
    assert attributes.message_deduplication_id is None
    assert record.md5_of_body == raw_event["Records"][0]["md5OfBody"]
    assert record.event_source == raw_event["Records"][0]["eventSource"]
    assert record.event_source_arn == raw_event["Records"][0]["eventSourceARN"]
    assert record.aws_region == raw_event["Records"][0]["awsRegion"]

    s3_event: S3Event = record.decoded_nested_s3_event
    s3_record = s3_event.record
    raw_body = json.loads(raw_event["Records"][0]["body"])

    assert s3_event.bucket_name == raw_body["Records"][0]["s3"]["bucket"]["name"]
    assert s3_event.object_key == raw_body["Records"][0]["s3"]["object"]["key"]
    raw_s3_record = raw_body["Records"][0]
    assert s3_record.aws_region == raw_s3_record["awsRegion"]
    assert s3_record.event_name == raw_s3_record["eventName"]
    assert s3_record.event_source == raw_s3_record["eventSource"]
    assert s3_record.event_time == raw_s3_record["eventTime"]
    assert s3_record.event_version == raw_s3_record["eventVersion"]
    assert s3_record.glacier_event_data is None
    assert s3_record.request_parameters.source_ip_address == raw_s3_record["requestParameters"]["sourceIPAddress"]
    assert s3_record.response_elements["x-amz-request-id"] == raw_s3_record["responseElements"]["x-amz-request-id"]
    assert s3_record.s3.s3_schema_version == raw_s3_record["s3"]["s3SchemaVersion"]
    assert s3_record.s3.bucket.arn == raw_s3_record["s3"]["bucket"]["arn"]
    assert s3_record.s3.bucket.name == raw_s3_record["s3"]["bucket"]["name"]
    assert (
        s3_record.s3.bucket.owner_identity.principal_id == raw_s3_record["s3"]["bucket"]["ownerIdentity"]["principalId"]
    )
    assert s3_record.s3.configuration_id == raw_s3_record["s3"]["configurationId"]
    assert s3_record.s3.get_object.etag == raw_s3_record["s3"]["object"]["eTag"]
    assert s3_record.s3.get_object.key == raw_s3_record["s3"]["object"]["key"]
    assert s3_record.s3.get_object.sequencer == raw_s3_record["s3"]["object"]["sequencer"]
    assert s3_record.s3.get_object.size == raw_s3_record["s3"]["object"]["size"]
    assert s3_record.s3.get_object.version_id == raw_s3_record["s3"]["object"]["versionId"]


def test_decode_nested_sns_event():
    raw_event = load_event("snsSqsEvent.json")
    event = SQSEvent(raw_event)

    records = list(event.records)
    record = records[0]
    attributes = record.attributes

    assert len(records) == 1
    assert record.message_id == raw_event["Records"][0]["messageId"]
    raw_attributes = raw_event["Records"][0]["attributes"]
    assert attributes.aws_trace_header is None
    assert attributes.approximate_receive_count == raw_attributes["ApproximateReceiveCount"]
    assert attributes.sent_timestamp == raw_attributes["SentTimestamp"]
    assert attributes.sender_id == raw_attributes["SenderId"]
    assert attributes.approximate_first_receive_timestamp == raw_attributes["ApproximateFirstReceiveTimestamp"]
    assert attributes.sequence_number is None
    assert attributes.message_group_id is None
    assert attributes.message_deduplication_id is None
    assert record.md5_of_body == raw_event["Records"][0]["md5OfBody"]
    assert record.event_source == raw_event["Records"][0]["eventSource"]
    assert record.event_source_arn == raw_event["Records"][0]["eventSourceARN"]
    assert record.aws_region == raw_event["Records"][0]["awsRegion"]

    sns_message: SNSMessage = record.decoded_nested_sns_event
    raw_body = json.loads(raw_event["Records"][0]["body"])
    message = json.loads(sns_message.message)

    assert sns_message.get_type == raw_body["Type"]
    assert sns_message.message_id == raw_body["MessageId"]
    assert sns_message.topic_arn == raw_body["TopicArn"]
    assert sns_message.timestamp == raw_body["Timestamp"]
    assert sns_message.signature_version == raw_body["SignatureVersion"]
    raw_message = json.loads(raw_body["Message"])
    assert message["message"] == raw_message["message"]
    assert message["username"] == raw_message["username"]
