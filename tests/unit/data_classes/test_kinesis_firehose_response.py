from aws_lambda_powertools.utilities.data_classes import (
    FirehoseStateOk,
    KinesisFirehoseEvent,
    KinesisFirehoseResponceFactory,
    KinesisFirehoseResponceRecordFactory,
)
from tests.functional.utils import load_event


def test_kinesis_firehose_response():
    raw_event = load_event("kinesisFirehoseKinesisEvent.json")
    parsed_event = KinesisFirehoseEvent(raw_event)

    result = []
    for record in parsed_event.records:
        # if data was delivered as json; caches loaded value
        data = record.data_as_text

        processed_record = KinesisFirehoseResponceRecordFactory(
            record_id=record.record_id,
            result=FirehoseStateOk,
            data=(data),
        )

        result.append(processed_record)
    response = KinesisFirehoseResponceFactory(result)

    res_records = list(response.records)
    assert len(res_records) == 2
    record_01, record_02 = res_records[:]
    record01_raw = raw_event["records"][0]
    assert record_01.result == FirehoseStateOk
    assert record_01.record_id == record01_raw["recordId"]
    assert record_01.data_as_bytes == b"Hello World"
    assert record_01.data_as_text == "Hello World"
    assert record_01.data == record01_raw["data"]
