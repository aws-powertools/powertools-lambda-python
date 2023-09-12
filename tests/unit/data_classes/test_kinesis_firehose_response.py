from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseDataTransformationRecord,
    KinesisFirehoseDataTransformationRecordMetadata,
    KinesisFirehoseDataTransformationResponse,
    KinesisFirehoseEvent,
)
from aws_lambda_powertools.utilities.serialization import base64_encode, base64_from_str
from tests.functional.utils import load_event


def test_kinesis_firehose_response():
    # GIVEN a Kinesis Firehose Event with two records
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    parsed_event = KinesisFirehoseEvent(data=raw_event)

    # WHEN we create a Data Transformation Response without changing the data
    response = KinesisFirehoseDataTransformationResponse()
    for record in parsed_event.records:
        metadata_partition = KinesisFirehoseDataTransformationRecordMetadata(partition_keys={"year": 2023})
        processed_record = KinesisFirehoseDataTransformationRecord(
            record_id=record.record_id,
            metadata=metadata_partition,
            data=record.data,
        )
        response.add_record(record=processed_record)

    # THEN we should have the same record data
    record_01, record_02 = response.records[0], response.records[1]
    raw_record_01, raw_record_02 = raw_event["records"][0], raw_event["records"][1]

    assert len(response.records) == 2

    assert record_01.result == "Ok"
    assert record_02.result == "Ok"

    assert record_01.record_id == raw_record_01["recordId"]
    assert record_02.record_id == raw_record_02["recordId"]

    assert record_01.data == raw_record_01["data"]
    assert record_02.data == raw_record_02["data"]

    assert record_01.metadata.partition_keys["year"] == 2023


def test_kinesis_firehose_create_response():
    # GIVEN a Kinesis Firehose Event with two records
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    parsed_event = KinesisFirehoseEvent(data=raw_event)

    # WHEN we create a Data Transformation Response changing the data
    # WHEN we add partitions keys

    arbitrary_data = "arbitrary data"

    response = KinesisFirehoseDataTransformationResponse()
    for record in parsed_event.records:
        metadata_partition = KinesisFirehoseDataTransformationRecordMetadata(partition_keys={"year": 2023})
        processed_record = record.build_data_transformation_response(
            result="Ok",
            metadata=metadata_partition,
            data=base64_from_str(arbitrary_data),
        )
        response.add_record(record=processed_record)

    # THEN we should have the same record data
    record_01, record_02 = response.records[0], response.records[1]
    raw_record_01, raw_record_02 = raw_event["records"][0], raw_event["records"][1]

    assert len(response.records) == 2

    assert record_01.result == "Ok"
    assert record_02.result == "Ok"

    assert record_01.record_id == raw_record_01["recordId"]
    assert record_02.record_id == raw_record_02["recordId"]

    assert record_01.data == base64_encode(arbitrary_data)
    assert record_02.data == base64_encode(arbitrary_data)

    assert record_01.metadata.partition_keys["year"] == 2023
