from typing import List

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
from tests.functional.utils import load_event
from tests.unit.parser.schemas import MyKinesisBusiness


@event_parser(model=MyKinesisBusiness, envelope=envelopes.KinesisDataStreamEnvelope)
def handle_kinesis(event: List[MyKinesisBusiness], _: LambdaContext):
    return event


@event_parser(model=KinesisDataStreamModel)
def handle_kinesis_no_envelope(event: KinesisDataStreamModel, _: LambdaContext):
    return event


def test_kinesis_trigger_bad_base64_event():
    raw_event = load_event("kinesisStreamEvent.json")

    raw_event["Records"][0]["kinesis"]["data"] = "bad"

    with pytest.raises(ValidationError):
        handle_kinesis_no_envelope(raw_event, LambdaContext())


def test_kinesis_trigger_event():
    raw_event = load_event("kinesisSingeEvent.json")
    parsed_event: MyKinesisBusiness = handle_kinesis(raw_event, LambdaContext())

    assert len(parsed_event) == 1
    record: KinesisDataStreamModel = parsed_event[0]
    assert record.message == "test message"
    assert record.username == "test"


def test_kinesis_trigger_event_no_envelope():
    raw_event = load_event("kinesisStreamEvent.json")
    parsed_event: KinesisDataStreamModel = handle_kinesis_no_envelope(raw_event, LambdaContext())

    records = parsed_event.Records
    assert len(records) == 2
    record: KinesisDataStreamModel = records[0]
    raw_record = raw_event["Records"][0]

    assert record.awsRegion == raw_record["awsRegion"]
    assert record.eventID == raw_record["eventID"]
    assert record.eventName == raw_record["eventName"]
    assert record.eventSource == raw_record["eventSource"]
    assert record.eventSourceARN == raw_record["eventSourceARN"]
    assert record.eventVersion == raw_record["eventVersion"]
    assert record.invokeIdentityArn == raw_record["invokeIdentityArn"]

    kinesis: KinesisDataStreamRecordPayload = record.kinesis
    assert kinesis.approximateArrivalTimestamp == raw_record["kinesis"]["approximateArrivalTimestamp"]
    assert kinesis.kinesisSchemaVersion == raw_record["kinesis"]["kinesisSchemaVersion"]
    assert kinesis.partitionKey == raw_record["kinesis"]["partitionKey"]
    assert kinesis.sequenceNumber == raw_record["kinesis"]["sequenceNumber"]
    assert kinesis.data == b"Hello, this is a test."


def test_validate_event_does_not_conform_with_model_no_envelope():
    raw_event: dict = {"hello": "s"}
    with pytest.raises(ValidationError):
        handle_kinesis_no_envelope(raw_event, LambdaContext())


def test_validate_event_does_not_conform_with_model():
    raw_event: dict = {"hello": "s"}
    with pytest.raises(ValidationError):
        handle_kinesis(raw_event, LambdaContext())


def test_kinesis_stream_event_cloudwatch_logs_data_extraction():
    # GIVEN a KinesisDataStreamModel is instantiated with CloudWatch Logs compressed data
    raw_event = load_event("kinesisStreamCloudWatchLogsEvent.json")
    stream_data = KinesisDataStreamModel(**raw_event)
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

    raw_event = load_event("kinesisStreamCloudWatchLogsEvent.json")
    stream_data = KinesisDataStreamModel(**raw_event)

    # WHEN decompress_zlib_record_data_as_json is used
    # THEN ValueError should be raised
    with pytest.raises(ValueError, match="We can only decompress bytes data"):
        for record in stream_data.Records:
            record.kinesis.data = DummyModel()
            record.decompress_zlib_record_data_as_json()
