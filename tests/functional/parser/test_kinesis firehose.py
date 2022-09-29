from typing import List

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, event_parser
from aws_lambda_powertools.utilities.parser.models import (
    KinesisFirehoseModel,
    KinesisFirehoseRecord,
    KinesisFirehoseRecordMetadata,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyKinesisFirehoseBusiness
from tests.functional.utils import load_event


@event_parser(model=MyKinesisFirehoseBusiness, envelope=envelopes.KinesisFirehoseEnvelope)
def handle_kinesis(event: List[MyKinesisFirehoseBusiness], _: LambdaContext):
    assert len(event) == 1
    assert event[0].Hello == "World"


@event_parser(model=KinesisFirehoseModel)
def handle_kinesis_no_envelope(event: KinesisFirehoseModel, _: LambdaContext):
    assert event.region == "us-east-2"
    assert event.invocationId == "2b4d1ad9-2f48-94bd-a088-767c317e994a"
    assert event.deliveryStreamArn == "arn:aws:firehose:us-east-2:123456789012:deliverystream/delivery-stream-name"
    assert event.sourceKinesisStreamArn is None

    records = list(event.records)
    assert len(records) == 2
    record_01: KinesisFirehoseRecord = records[0]

    convert_time = int(round(record_01.approximateArrivalTimestamp.timestamp() * 1000))
    assert convert_time == 1510772160000
    assert record_01.recordId == "record1"
    assert record_01.data == b"Hello World"

    metadata_01: KinesisFirehoseRecordMetadata = record_01.kinesisRecordMetadata
    assert metadata_01.partitionKey == "4d1ad2b9-24f8-4b9d-a088-76e9947c317a"
    assert metadata_01.subsequenceNumber == ""
    assert metadata_01.shardId == "shardId-000000000000"
    assert metadata_01.approximateArrivalTimestamp == "2012-04-23T18:25:43.511Z"
    assert metadata_01.sequenceNumber == "49546986683135544286507457936321625675700192471156785154"

    record_02: KinesisFirehoseRecord = records[1]
    convert_time = int(round(record_02.approximateArrivalTimestamp.timestamp() * 1000))
    assert convert_time == 151077216000
    assert record_02.recordId == "record2"
    assert record_02.data == b'{"Hello": "World"}'

    metadata_02: KinesisFirehoseRecordMetadata = record_02.kinesisRecordMetadata
    assert metadata_02.partitionKey == "4d1ad2b9-24f8-4b9d-a088-76e9947c318a"
    assert metadata_02.subsequenceNumber == ""
    assert metadata_02.shardId == "shardId-000000000001"
    assert metadata_02.approximateArrivalTimestamp == "2012-04-23T19:25:43.511Z"
    assert metadata_02.sequenceNumber == "49546986683135544286507457936321625675700192471156785155"


def test_kinesis_trigger_event():
    event_dict = load_event("kinesisFirehoseEvent.json")
    event_dict["records"].pop(0)  # remove first item since the payload is bytes and we want to test payload json class
    handle_kinesis(event_dict, LambdaContext())


def test_kinesis_trigger_event_no_envelope():
    event_dict = load_event("kinesisFirehoseEvent.json")
    handle_kinesis_no_envelope(event_dict, LambdaContext())


def test_kinesis_trigger_bad_base64_event():
    event_dict = load_event("kinesisFirehoseEvent.json")
    event_dict["records"][0]["data"] = {"bad base64"}
    with pytest.raises(ValidationError):
        handle_kinesis_no_envelope(event_dict, LambdaContext())
