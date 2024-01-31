import pytest

from aws_lambda_powertools.utilities.data_classes import KafkaEvent
from tests.functional.utils import load_event


def test_kafka_msk_event():
    raw_event = load_event("kafkaEventMsk.json")
    parsed_event = KafkaEvent(raw_event)

    assert parsed_event.event_source == raw_event["eventSource"]
    assert parsed_event.event_source_arn == raw_event["eventSourceArn"]

    bootstrap_servers_raw = raw_event["bootstrapServers"]

    bootstrap_servers_list = raw_event["bootstrapServers"].split(",")

    assert parsed_event.bootstrap_servers == bootstrap_servers_raw
    assert parsed_event.decoded_bootstrap_servers == bootstrap_servers_list

    records = list(parsed_event.records)
    assert len(records) == 1
    record = records[0]
    raw_record = raw_event["records"]["mytopic-0"][0]
    assert record.topic == raw_record["topic"]
    assert record.partition == raw_record["partition"]
    assert record.offset == raw_record["offset"]
    assert record.timestamp == raw_record["timestamp"]
    assert record.timestamp_type == raw_record["timestampType"]
    assert record.decoded_key == b"recordKey"
    assert record.value == raw_record["value"]
    assert record.json_value == {"key": "value"}
    assert record.decoded_headers == {"headerKey": b"headerValue"}
    assert record.get_header_value("HeaderKey", case_sensitive=False) == b"headerValue"

    assert parsed_event.record == records[0]


def test_kafka_self_managed_event():
    raw_event = load_event("kafkaEventSelfManaged.json")
    parsed_event = KafkaEvent(raw_event)

    assert parsed_event.event_source == raw_event["eventSource"]

    bootstrap_servers_raw = raw_event["bootstrapServers"]

    bootstrap_servers_list = raw_event["bootstrapServers"].split(",")

    assert parsed_event.bootstrap_servers == bootstrap_servers_raw
    assert parsed_event.decoded_bootstrap_servers == bootstrap_servers_list

    records = list(parsed_event.records)
    assert len(records) == 1
    record = records[0]
    raw_record = raw_event["records"]["mytopic-0"][0]
    assert record.topic == raw_record["topic"]
    assert record.partition == raw_record["partition"]
    assert record.offset == raw_record["offset"]
    assert record.timestamp == raw_record["timestamp"]
    assert record.timestamp_type == raw_record["timestampType"]
    assert record.decoded_key == b"recordKey"
    assert record.value == raw_record["value"]
    assert record.json_value == {"key": "value"}
    assert record.decoded_headers == {"headerKey": b"headerValue"}
    assert record.get_header_value("HeaderKey", case_sensitive=False) == b"headerValue"

    assert parsed_event.record == records[0]


def test_kafka_record_property_with_stopiteration_error():
    # GIVEN a kafka event with one record
    raw_event = load_event("kafkaEventMsk.json")
    parsed_event = KafkaEvent(raw_event)

    # WHEN calling record property twice
    # THEN raise StopIteration
    with pytest.raises(StopIteration):
        assert parsed_event.record.topic is not None
        assert parsed_event.record.partition is not None
