from aws_lambda_powertools.utilities.data_classes import KinesisFirehoseEvent
from tests.functional.utils import load_event


def test_kinesis_firehose_kinesis_event():
    event = KinesisFirehoseEvent(load_event("kinesisFirehoseKinesisEvent.json"))

    assert event.region == "us-east-2"
    assert event.invocation_id == "2b4d1ad9-2f48-94bd-a088-767c317e994a"
    assert event.delivery_stream_arn == "arn:aws:firehose:us-east-2:123456789012:deliverystream/delivery-stream-name"
    assert event.source_kinesis_stream_arn == "arn:aws:kinesis:us-east-1:123456789012:stream/kinesis-source"

    records = list(event.records)
    assert len(records) == 2
    record_01, record_02 = records[:]

    assert record_01.approximate_arrival_timestamp == 1664028820148
    assert record_01.record_id == "record1"
    assert record_01.data == "SGVsbG8gV29ybGQ="
    assert record_01.data_as_bytes == b"Hello World"
    assert record_01.data_as_text == "Hello World"

    assert record_01.metadata.shard_id == "shardId-000000000000"
    assert record_01.metadata.partition_key == "4d1ad2b9-24f8-4b9d-a088-76e9947c317a"
    assert record_01.metadata.approximate_arrival_timestamp == 1664028820148
    assert record_01.metadata.sequence_number == "49546986683135544286507457936321625675700192471156785154"
    assert record_01.metadata.subsequence_number == ""

    assert record_02.approximate_arrival_timestamp == 1664028793294
    assert record_02.record_id == "record2"
    assert record_02.data == "eyJIZWxsbyI6ICJXb3JsZCJ9"
    assert record_02.data_as_bytes == b'{"Hello": "World"}'
    assert record_02.data_as_text == '{"Hello": "World"}'
    assert record_02.data_as_json == {"Hello": "World"}

    assert record_02.metadata.shard_id == "shardId-000000000001"
    assert record_02.metadata.partition_key == "4d1ad2b9-24f8-4b9d-a088-76e9947c318a"
    assert record_02.metadata.approximate_arrival_timestamp == 1664028793294
    assert record_02.metadata.sequence_number == "49546986683135544286507457936321625675700192471156785155"
    assert record_02.metadata.subsequence_number == ""


def test_kinesis_firehose_put_event():
    event = KinesisFirehoseEvent(load_event("kinesisFirehosePutEvent.json"))

    assert event.region == "us-east-2"
    assert event.invocation_id == "2b4d1ad9-2f48-94bd-a088-767c317e994a"
    assert event.delivery_stream_arn == "arn:aws:firehose:us-east-2:123456789012:deliverystream/delivery-stream-name"
    assert event.source_kinesis_stream_arn is None

    records = list(event.records)
    assert len(records) == 2
    record_01, record_02 = records[:]

    assert record_01.approximate_arrival_timestamp == 1664029185290
    assert record_01.record_id == "record1"
    assert record_01.data == "SGVsbG8gV29ybGQ="
    assert record_01.data_as_bytes == b"Hello World"
    assert record_01.data_as_text == "Hello World"
    assert record_01.metadata is None

    assert record_02.approximate_arrival_timestamp == 1664029186945
    assert record_02.record_id == "record2"
    assert record_02.data == "eyJIZWxsbyI6ICJXb3JsZCJ9"
    assert record_02.data_as_bytes == b'{"Hello": "World"}'
    assert record_02.data_as_text == '{"Hello": "World"}'
    assert record_02.data_as_json == {"Hello": "World"}
    assert record_02.metadata is None
