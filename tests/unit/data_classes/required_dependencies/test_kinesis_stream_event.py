import base64
import json

from aws_lambda_powertools.utilities.data_classes import KinesisStreamEvent
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import (
    extract_cloudwatch_logs_from_event,
    extract_cloudwatch_logs_from_record,
)
from tests.functional.utils import load_event


def test_kinesis_stream_event():
    raw_event = load_event("kinesisStreamEvent.json")
    parsed_event = KinesisStreamEvent(raw_event)

    records = list(parsed_event.records)
    assert len(records) == 2
    record = records[0]

    record_raw = raw_event["Records"][0]

    assert record.aws_region == record_raw["awsRegion"]
    assert record.event_id == record_raw["eventID"]
    assert record.event_name == record_raw["eventName"]
    assert record.event_source == record_raw["eventSource"]
    assert record.event_source_arn == record_raw["eventSourceARN"]
    assert record.event_version == record_raw["eventVersion"]
    assert record.invoke_identity_arn == record_raw["invokeIdentityArn"]

    kinesis = record.kinesis
    kinesis_raw = raw_event["Records"][0]["kinesis"]
    assert kinesis._data["kinesis"] == kinesis_raw

    assert kinesis.approximate_arrival_timestamp == kinesis_raw["approximateArrivalTimestamp"]
    assert kinesis.data == kinesis_raw["data"]
    assert kinesis.kinesis_schema_version == kinesis_raw["kinesisSchemaVersion"]
    assert kinesis.partition_key == kinesis_raw["partitionKey"]
    assert kinesis.sequence_number == kinesis_raw["sequenceNumber"]

    assert kinesis.data_as_bytes() == b"Hello, this is a test."
    assert kinesis.data_as_text() == "Hello, this is a test."


def test_kinesis_stream_event_json_data():
    json_value = {"test": "value"}
    data = base64.b64encode(bytes(json.dumps(json_value), "utf-8")).decode("utf-8")
    event = KinesisStreamEvent({"Records": [{"kinesis": {"data": data}}]})
    record = next(event.records)
    assert record.kinesis.data_as_json() == json_value


def test_kinesis_stream_event_cloudwatch_logs_data_extraction():
    event = KinesisStreamEvent(load_event("kinesisStreamCloudWatchLogsEvent.json"))
    extracted_logs = extract_cloudwatch_logs_from_event(event)
    individual_logs = [extract_cloudwatch_logs_from_record(record) for record in event.records]

    assert len(extracted_logs) == len(individual_logs)
