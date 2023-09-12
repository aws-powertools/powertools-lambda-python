from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseDataTransformationRecord,
    KinesisFirehoseDataTransformationRecordMetadata,
    KinesisFirehoseDataTransformationResponse,
    KinesisFirehoseEvent,
)
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
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    parsed_event = KinesisFirehoseEvent(data=raw_event)

    response = KinesisFirehoseDataTransformationResponse()
    for record in parsed_event.records:
        # if data was delivered as json; caches loaded value
        data = record.data_as_text
        metadata_partition = KinesisFirehoseDataTransformationRecordMetadata(partition_keys={"year": 2023})
        processed_record = record.build_data_transformation_response(
            result="Ok",
            metadata=metadata_partition,
        )
        processed_record.data_from_text(data=data)
        response.add_record(record=processed_record)
    response_dict = response.asdict()

    res_records = list(response_dict["records"])
    assert len(res_records) == 2
    record_01, record_02 = res_records[:]
    record01_raw = raw_event["records"][0]
    assert record_01["result"] == "Ok"
    assert record_01["recordId"] == record01_raw["recordId"]
    assert record_01["data"] == record01_raw["data"]
    assert record_01["metadata"]["partitionKeys"]["year"] == 2023

    assert response.records[0].data_as_bytes == b"Hello World"
    assert response.records[0].data_as_text == "Hello World"
