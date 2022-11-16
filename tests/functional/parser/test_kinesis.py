from typing import Any, List

import pytest

from aws_lambda_powertools.utilities.parser import (
    BaseModel,
    ValidationError,
    envelopes,
    event_parser,
)
from aws_lambda_powertools.utilities.parser.models import (
    KinesisDataStreamModel,
    KinesisDataStreamRecordPayload,
)
from aws_lambda_powertools.utilities.parser.models.cloudwatch import (
    CloudWatchLogsDecode,
)
from aws_lambda_powertools.utilities.parser.models.kinesis import (
    extract_cloudwatch_logs_from_event,
    extract_cloudwatch_logs_from_record,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyKinesisBusiness
from tests.functional.utils import load_event


@event_parser(model=MyKinesisBusiness, envelope=envelopes.KinesisDataStreamEnvelope)
def handle_kinesis(event: List[MyKinesisBusiness], _: LambdaContext):
    assert len(event) == 1
    record: KinesisDataStreamModel = event[0]
    assert record.message == "test message"
    assert record.username == "test"


@event_parser(model=KinesisDataStreamModel)
def handle_kinesis_no_envelope(event: KinesisDataStreamModel, _: LambdaContext):
    records = event.Records
    assert len(records) == 2
    record: KinesisDataStreamModel = records[0]

    assert record.awsRegion == "us-east-2"
    assert record.eventID == "shardId-000000000006:49590338271490256608559692538361571095921575989136588898"
    assert record.eventName == "aws:kinesis:record"
    assert record.eventSource == "aws:kinesis"
    assert record.eventSourceARN == "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream"
    assert record.eventVersion == "1.0"
    assert record.invokeIdentityArn == "arn:aws:iam::123456789012:role/lambda-role"

    kinesis: KinesisDataStreamRecordPayload = record.kinesis
    assert kinesis.approximateArrivalTimestamp == 1545084650.987
    assert kinesis.kinesisSchemaVersion == "1.0"
    assert kinesis.partitionKey == "1"
    assert kinesis.sequenceNumber == "49590338271490256608559692538361571095921575989136588898"
    assert kinesis.data == b"Hello, this is a test."


def test_kinesis_trigger_event():
    event_dict = {
        "Records": [
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                    "data": "eyJtZXNzYWdlIjogInRlc3QgbWVzc2FnZSIsICJ1c2VybmFtZSI6ICJ0ZXN0In0=",
                    "approximateArrivalTimestamp": 1545084650.987,
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:49590338271490256608559692538361571095921575989136588898",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-role",
                "awsRegion": "us-east-2",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream",
            }
        ]
    }

    handle_kinesis(event_dict, LambdaContext())


def test_kinesis_trigger_bad_base64_event():
    event_dict = {
        "Records": [
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                    "data": "bad",
                    "approximateArrivalTimestamp": 1545084650.987,
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:49590338271490256608559692538361571095921575989136588898",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-role",
                "awsRegion": "us-east-2",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream",
            }
        ]
    }
    with pytest.raises(ValidationError):
        handle_kinesis_no_envelope(event_dict, LambdaContext())


def test_kinesis_trigger_event_no_envelope():
    event_dict = load_event("kinesisStreamEvent.json")
    handle_kinesis_no_envelope(event_dict, LambdaContext())


def test_validate_event_does_not_conform_with_model_no_envelope():
    event_dict: Any = {"hello": "s"}
    with pytest.raises(ValidationError):
        handle_kinesis_no_envelope(event_dict, LambdaContext())


def test_validate_event_does_not_conform_with_model():
    event_dict: Any = {"hello": "s"}
    with pytest.raises(ValidationError):
        handle_kinesis(event_dict, LambdaContext())


def test_kinesis_stream_event_cloudwatch_logs_data_extraction():
    # GIVEN a KinesisDataStreamModel is instantiated with CloudWatch Logs compressed data
    event_dict = load_event("kinesisStreamCloudWatchLogsEvent.json")
    stream_data = KinesisDataStreamModel(**event_dict)
    single_record = stream_data.Records[0]

    # WHEN we try to extract CloudWatch Logs from KinesisDataStreamRecordPayload model
    extracted_logs = extract_cloudwatch_logs_from_event(stream_data)
    individual_logs = [extract_cloudwatch_logs_from_record(record) for record in stream_data.Records]
    single_log = extract_cloudwatch_logs_from_record(single_record)

    # THEN we should have extracted any potential logs as CloudWatchLogsDecode models
    assert len(extracted_logs) == len(individual_logs)
    assert isinstance(single_log, CloudWatchLogsDecode)


def test_kinesis_stream_event_cloudwatch_logs_data_extraction_fails_with_custom_model():
    # GIVEN a custom model replaces Kinesis Record Data bytes
    class DummyModel(BaseModel):
        ...

    event_dict = load_event("kinesisStreamCloudWatchLogsEvent.json")
    stream_data = KinesisDataStreamModel(**event_dict)

    # WHEN decompress_zlib_record_data_as_json is used
    # THEN ValueError should be raised
    with pytest.raises(ValueError, match="We can only decompress bytes data"):
        for record in stream_data.Records:
            record.kinesis.data = DummyModel()
            record.decompress_zlib_record_data_as_json()
