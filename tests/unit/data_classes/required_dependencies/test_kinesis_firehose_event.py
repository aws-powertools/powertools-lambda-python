from aws_lambda_powertools.utilities.data_classes import KinesisFirehoseEvent
from tests.functional.utils import load_event


def test_kinesis_firehose_kinesis_event():
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    parsed_event = KinesisFirehoseEvent(raw_event)

    assert parsed_event.region == raw_event["region"]
    assert parsed_event.invocation_id == raw_event["invocationId"]
    assert parsed_event.delivery_stream_arn == raw_event["deliveryStreamArn"]
    assert parsed_event.source_kinesis_stream_arn == raw_event["sourceKinesisStreamArn"]

    records = list(parsed_event.records)
    assert len(records) == 2
    record_01, record_02 = records[:]

    record01_raw = raw_event["records"][0]
    assert record_01.approximate_arrival_timestamp == record01_raw["approximateArrivalTimestamp"]
    assert record_01.record_id == record01_raw["recordId"]
    assert record_01.data == record01_raw["data"]
    assert record_01.data_as_bytes == b"Hello World"
    assert record_01.data_as_text == "Hello World"

    assert record_01.metadata.shard_id == record01_raw["kinesisRecordMetadata"]["shardId"]
    assert record_01.metadata.partition_key == record01_raw["kinesisRecordMetadata"]["partitionKey"]
    assert (
        record_01.metadata.approximate_arrival_timestamp
        == record01_raw["kinesisRecordMetadata"]["approximateArrivalTimestamp"]
    )
    assert record_01.metadata.sequence_number == record01_raw["kinesisRecordMetadata"]["sequenceNumber"]
    assert record_01.metadata.subsequence_number == record01_raw["kinesisRecordMetadata"]["subsequenceNumber"]

    record02_raw = raw_event["records"][1]
    assert record_02.approximate_arrival_timestamp == record02_raw["approximateArrivalTimestamp"]
    assert record_02.record_id == record02_raw["recordId"]
    assert record_02.data == record02_raw["data"]
    assert record_02.data_as_bytes == b'{"Hello": "World"}'
    assert record_02.data_as_text == '{"Hello": "World"}'
    assert record_02.data_as_json == {"Hello": "World"}

    assert record_02.metadata.shard_id == record02_raw["kinesisRecordMetadata"]["shardId"]
    assert record_02.metadata.partition_key == record02_raw["kinesisRecordMetadata"]["partitionKey"]
    assert (
        record_02.metadata.approximate_arrival_timestamp
        == record02_raw["kinesisRecordMetadata"]["approximateArrivalTimestamp"]
    )
    assert record_02.metadata.sequence_number == record02_raw["kinesisRecordMetadata"]["sequenceNumber"]
    assert record_02.metadata.subsequence_number == record02_raw["kinesisRecordMetadata"]["subsequenceNumber"]


def test_kinesis_firehose_put_event():
    raw_event = load_event("kinesisFirehosePutEvent.json")
    parsed_event = KinesisFirehoseEvent(raw_event)

    assert parsed_event.region == raw_event["region"]
    assert parsed_event.invocation_id == raw_event["invocationId"]
    assert parsed_event.delivery_stream_arn == raw_event["deliveryStreamArn"]
    assert parsed_event.source_kinesis_stream_arn is None

    records = list(parsed_event.records)
    assert len(records) == 2
    record_01, record_02 = records[:]

    record01_raw = raw_event["records"][0]
    assert record_01.approximate_arrival_timestamp == record01_raw["approximateArrivalTimestamp"]
    assert record_01.record_id == record01_raw["recordId"]
    assert record_01.data == record01_raw["data"]
    assert record_01.data_as_bytes == b"Hello World"
    assert record_01.data_as_text == "Hello World"
    assert record_01.metadata is None

    record02_raw = raw_event["records"][1]
    assert record_02.approximate_arrival_timestamp == record02_raw["approximateArrivalTimestamp"]
    assert record_02.record_id == record02_raw["recordId"]
    assert record_02.data == record02_raw["data"]
    assert record_02.data_as_bytes == b'{"Hello": "World"}'
    assert record_02.data_as_text == '{"Hello": "World"}'
    assert record_02.data_as_json == {"Hello": "World"}
    assert record_02.metadata is None
