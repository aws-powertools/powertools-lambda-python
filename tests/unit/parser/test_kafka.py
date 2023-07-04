from typing import List

from aws_lambda_powertools.utilities.parser import envelopes, event_parser
from aws_lambda_powertools.utilities.parser.models import (
    KafkaMskEventModel,
    KafkaRecordModel,
    KafkaSelfManagedEventModel,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.utils import load_event
from tests.unit.parser.schemas import MyLambdaKafkaBusiness


@event_parser(model=MyLambdaKafkaBusiness, envelope=envelopes.KafkaEnvelope)
def handle_lambda_kafka_with_envelope(event: List[MyLambdaKafkaBusiness], _: LambdaContext):
    return event


@event_parser(model=KafkaSelfManagedEventModel)
def handle_kafka_event(event: KafkaSelfManagedEventModel, _: LambdaContext):
    return event


def test_kafka_msk_event_with_envelope():
    raw_event = load_event("kafkaEventMsk.json")
    parsed_event: MyLambdaKafkaBusiness = handle_lambda_kafka_with_envelope(raw_event, LambdaContext())

    assert parsed_event[0].key == "value"
    assert len(parsed_event) == 1


def test_kafka_self_managed_event_with_envelope():
    raw_event = load_event("kafkaEventSelfManaged.json")
    parsed_event: MyLambdaKafkaBusiness = handle_lambda_kafka_with_envelope(raw_event, LambdaContext())

    assert parsed_event[0].key == "value"
    assert len(parsed_event) == 1


def test_self_managed_kafka_event():
    raw_event = load_event("kafkaEventSelfManaged.json")
    parsed_event: KafkaSelfManagedEventModel = handle_kafka_event(raw_event, LambdaContext())

    assert parsed_event.eventSource == raw_event["eventSource"]

    assert parsed_event.bootstrapServers == raw_event["bootstrapServers"].split(",")

    records = list(parsed_event.records["mytopic-0"])
    assert len(records) == 1
    record: KafkaRecordModel = records[0]
    raw_record = raw_event["records"]["mytopic-0"][0]
    assert record.topic == raw_record["topic"]
    assert record.partition == raw_record["partition"]
    assert record.offset == raw_record["offset"]
    assert record.timestamp is not None
    convert_time = int(round(record.timestamp.timestamp() * 1000))
    assert convert_time == raw_record["timestamp"]
    assert record.timestampType == raw_record["timestampType"]
    assert record.key == b"recordKey"
    assert record.value == '{"key":"value"}'
    assert len(record.headers) == 1
    assert record.headers[0]["headerKey"] == b"headerValue"


@event_parser(model=KafkaMskEventModel)
def handle_msk_event(event: KafkaMskEventModel, _: LambdaContext):
    return event


def test_kafka_msk_event():
    raw_event = load_event("kafkaEventMsk.json")
    parsed_event: KafkaMskEventModel = handle_msk_event(raw_event, LambdaContext())

    assert parsed_event.eventSource == raw_event["eventSource"]
    assert parsed_event.bootstrapServers == raw_event["bootstrapServers"].split(",")
    assert parsed_event.eventSourceArn == raw_event["eventSourceArn"]

    records = list(parsed_event.records["mytopic-0"])
    assert len(records) == 1
    record: KafkaRecordModel = records[0]
    raw_record = raw_event["records"]["mytopic-0"][0]
    assert record.topic == raw_record["topic"]
    assert record.partition == raw_record["partition"]
    assert record.offset == raw_record["offset"]
    assert record.timestamp is not None
    convert_time = int(round(record.timestamp.timestamp() * 1000))
    assert convert_time == raw_record["timestamp"]
    assert record.timestampType == raw_record["timestampType"]
    assert record.key == b"recordKey"
    assert record.value == '{"key":"value"}'
    assert len(record.headers) == 1
    assert record.headers[0]["headerKey"] == b"headerValue"
