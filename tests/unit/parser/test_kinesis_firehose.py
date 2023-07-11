import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, parse
from aws_lambda_powertools.utilities.parser.models import (
    KinesisFirehoseModel,
    KinesisFirehoseRecord,
    KinesisFirehoseRecordMetadata,
    KinesisFirehoseSqsModel,
    KinesisFirehoseSqsRecord,
)
from tests.functional.utils import load_event
from tests.unit.parser.schemas import MyKinesisFirehoseBusiness


def test_firehose_sqs_wrapped_message_event():
    raw_event = load_event("kinesisFirehoseSQSEvent.json")
    parsed_event: KinesisFirehoseSqsModel = KinesisFirehoseSqsModel(**raw_event)

    assert parsed_event.region == raw_event["region"]
    assert parsed_event.invocationId == raw_event["invocationId"]
    assert parsed_event.deliveryStreamArn == raw_event["deliveryStreamArn"]

    records = list(parsed_event.records)
    assert len(records) == 1

    record_01: KinesisFirehoseSqsRecord = records[0]
    assert record_01.data.messageId == "5ab807d4-5644-4c55-97a3-47396635ac74"
    assert record_01.data.receiptHandle == "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a..."
    assert record_01.data.body == "Test message."
    assert record_01.data.attributes.ApproximateReceiveCount == "1"
    assert record_01.data.attributes.SenderId == "AIDAIENQZJOLO23YVJ4VO"


def test_firehose_trigger_event():
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    raw_event["records"].pop(0)  # remove first item since the payload is bytes and we want to test payload json class
    parsed_event: MyKinesisFirehoseBusiness = parse(
        event=raw_event,
        model=MyKinesisFirehoseBusiness,
        envelope=envelopes.KinesisFirehoseEnvelope,
    )

    assert len(parsed_event) == 1
    assert parsed_event[0].Hello == "World"


def test_firehose_trigger_event_kinesis_no_envelope():
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    parsed_event: KinesisFirehoseModel = KinesisFirehoseModel(**raw_event)

    assert parsed_event.region == raw_event["region"]
    assert parsed_event.invocationId == raw_event["invocationId"]
    assert parsed_event.deliveryStreamArn == raw_event["deliveryStreamArn"]
    assert parsed_event.sourceKinesisStreamArn == raw_event["sourceKinesisStreamArn"]

    records = list(parsed_event.records)
    assert len(records) == 2
    record_01: KinesisFirehoseRecord = records[0]
    assert record_01.approximateArrivalTimestamp == 1664028820148
    assert record_01.recordId == "record1"
    assert record_01.data == b"Hello World"

    metadata_01: KinesisFirehoseRecordMetadata = record_01.kinesisRecordMetadata
    assert metadata_01.partitionKey == "4d1ad2b9-24f8-4b9d-a088-76e9947c317a"
    assert metadata_01.subsequenceNumber == ""
    assert metadata_01.shardId == "shardId-000000000000"
    assert metadata_01.approximateArrivalTimestamp == 1664028820148
    assert metadata_01.sequenceNumber == "49546986683135544286507457936321625675700192471156785154"

    record_02: KinesisFirehoseRecord = records[1]
    assert record_02.approximateArrivalTimestamp == 1664028793294
    assert record_02.recordId == "record2"
    assert record_02.data == b'{"Hello": "World"}'

    metadata_02: KinesisFirehoseRecordMetadata = record_02.kinesisRecordMetadata
    assert metadata_02.partitionKey == "4d1ad2b9-24f8-4b9d-a088-76e9947c318a"
    assert metadata_02.subsequenceNumber == ""
    assert metadata_02.shardId == "shardId-000000000001"
    assert metadata_02.approximateArrivalTimestamp == 1664028793294
    assert metadata_02.sequenceNumber == "49546986683135544286507457936321625675700192471156785155"


def test_firehose_trigger_event_put_no_envelope():
    raw_event = load_event("kinesisFirehosePutEvent.json")
    parsed_event: KinesisFirehoseModel = KinesisFirehoseModel(**raw_event)

    assert parsed_event.region == raw_event["region"]
    assert parsed_event.invocationId == raw_event["invocationId"]
    assert parsed_event.deliveryStreamArn == raw_event["deliveryStreamArn"]

    records = list(parsed_event.records)
    assert len(records) == 2

    record_01: KinesisFirehoseRecord = records[0]
    assert record_01.approximateArrivalTimestamp == 1664029185290
    assert record_01.recordId == "record1"
    assert record_01.data == b"Hello World"

    record_02: KinesisFirehoseRecord = records[1]
    assert record_02.approximateArrivalTimestamp == 1664029186945
    assert record_02.recordId == "record2"
    assert record_02.data == b'{"Hello": "World"}'


def test_kinesis_trigger_bad_base64_event():
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    raw_event["records"][0]["data"] = {"bad base64"}
    with pytest.raises(ValidationError):
        KinesisFirehoseModel(**raw_event)


def test_kinesis_trigger_bad_timestamp_event():
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    raw_event["records"][0]["approximateArrivalTimestamp"] = -1
    with pytest.raises(ValidationError):
        KinesisFirehoseModel(**raw_event)


def test_kinesis_trigger_bad_metadata_timestamp_event():
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    raw_event["records"][0]["kinesisRecordMetadata"]["approximateArrivalTimestamp"] = "-1"
    with pytest.raises(ValidationError):
        KinesisFirehoseModel(**raw_event)
