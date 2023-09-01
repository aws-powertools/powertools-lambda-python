from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseEvent,
    KinesisFirehoseResponse,
    KinesisFirehoseResponseRecord,
)
from tests.functional.utils import load_event


def test_kinesis_firehose_response():
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    parsed_event = KinesisFirehoseEvent(data=raw_event)

    response = KinesisFirehoseResponse()
    for record in parsed_event.records:
        # if data was delivered as json; caches loaded value
        data = record.data_as_text

        processed_record = KinesisFirehoseResponseRecord(
            record_id=record.record_id,
            result="Ok",
        )
        processed_record.data_from_text(data=data)
        response.add_record(record=processed_record)
    response_dict = response.asdict

    res_records = list(response_dict["records"])
    assert len(res_records) == 2
    record_01, record_02 = res_records[:]
    record01_raw = raw_event["records"][0]
    assert record_01["result"] == "Ok"
    assert record_01["recordId"] == record01_raw["recordId"]
    assert record_01["data"] == record01_raw["data"]

    assert response.records[0].data_as_bytes == b"Hello World"
    assert response.records[0].data_as_text == "Hello World"


def test_kinesis_firehose_create_response():
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    parsed_event = KinesisFirehoseEvent(data=raw_event)

    response = KinesisFirehoseResponse()
    for record in parsed_event.records:
        # if data was delivered as json; caches loaded value
        data = record.data_as_text

        processed_record = record.create_firehose_response_record(
            result="Ok",
        )
        processed_record.data_from_text(data=data)
        response.add_record(record=processed_record)
    response_dict = response.asdict

    res_records = list(response_dict["records"])
    assert len(res_records) == 2
    record_01, record_02 = res_records[:]
    record01_raw = raw_event["records"][0]
    assert record_01["result"] == "Ok"
    assert record_01["recordId"] == record01_raw["recordId"]
    assert record_01["data"] == record01_raw["data"]

    assert response.records[0].data_as_bytes == b"Hello World"
    assert response.records[0].data_as_text == "Hello World"
