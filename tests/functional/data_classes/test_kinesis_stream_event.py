import base64
import json

from aws_lambda_powertools.utilities.data_classes import KinesisStreamEvent
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import (
    extract_cloudwatch_logs_from_event,
    extract_cloudwatch_logs_from_record,
)
from tests.functional.utils import load_event


def test_kinesis_stream_event():
    event = KinesisStreamEvent(load_event("kinesisStreamEvent.json"))

    records = list(event.records)
    assert len(records) == 2
    record = records[0]

    assert record.aws_region == "us-east-2"
    assert record.event_id == "shardId-000000000006:49590338271490256608559692538361571095921575989136588898"
    assert record.event_name == "aws:kinesis:record"
    assert record.event_source == "aws:kinesis"
    assert record.event_source_arn == "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream"
    assert record.event_version == "1.0"
    assert record.invoke_identity_arn == "arn:aws:iam::123456789012:role/lambda-role"

    kinesis = record.kinesis
    assert kinesis._data["kinesis"] == event["Records"][0]["kinesis"]

    assert kinesis.approximate_arrival_timestamp == 1545084650.987
    assert kinesis.data == event["Records"][0]["kinesis"]["data"]
    assert kinesis.kinesis_schema_version == "1.0"
    assert kinesis.partition_key == "1"
    assert kinesis.sequence_number == "49590338271490256608559692538361571095921575989136588898"

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
