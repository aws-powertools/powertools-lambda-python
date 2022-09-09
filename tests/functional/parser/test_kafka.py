from typing import List

from aws_lambda_powertools.utilities.parser import envelopes, event_parser
from aws_lambda_powertools.utilities.parser.models import (
    KafkaMskEventModel,
    KafkaRecordModel,
    KafkaSelfManagedEventModel,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyLambdaKafkaBusiness
from tests.functional.utils import load_event


@event_parser(model=MyLambdaKafkaBusiness, envelope=envelopes.KafkaEnvelope)
def handle_lambda_kafka_with_envelope(event: List[MyLambdaKafkaBusiness], _: LambdaContext):
    assert event[0].key == "value"
    assert len(event) == 1


@event_parser(model=KafkaSelfManagedEventModel)
def handle_kafka_event(event: KafkaSelfManagedEventModel, _: LambdaContext):
    return event


def test_kafka_msk_event_with_envelope():
    event = load_event("kafkaEventMsk.json")
    handle_lambda_kafka_with_envelope(event, LambdaContext())


def test_kafka_self_managed_event_with_envelope():
    event = load_event("kafkaEventSelfManaged.json")
    handle_lambda_kafka_with_envelope(event, LambdaContext())


def test_self_managed_kafka_event():
    json_event = load_event("kafkaEventSelfManaged.json")
    event: KafkaSelfManagedEventModel = handle_kafka_event(json_event, LambdaContext())
    assert event.eventSource == "aws:SelfManagedKafka"
    bootstrap_servers = [
        "b-2.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092",
        "b-1.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092",
    ]
    assert event.bootstrapServers == bootstrap_servers

    records = list(event.records["mytopic-0"])
    assert len(records) == 1
    record: KafkaRecordModel = records[0]
    assert record.topic == "mytopic"
    assert record.partition == 0
    assert record.offset == 15
    assert record.timestamp is not None
    convert_time = int(round(record.timestamp.timestamp() * 1000))
    assert convert_time == 1545084650987
    assert record.timestampType == "CREATE_TIME"
    assert record.key == b"recordKey"
    assert record.value == '{"key":"value"}'
    assert len(record.headers) == 1
    assert record.headers[0]["headerKey"] == b"headerValue"


@event_parser(model=KafkaMskEventModel)
def handle_msk_event(event: KafkaMskEventModel, _: LambdaContext):
    return event


def test_kafka_msk_event():
    json_event = load_event("kafkaEventMsk.json")
    event: KafkaMskEventModel = handle_msk_event(json_event, LambdaContext())
    assert event.eventSource == "aws:kafka"
    bootstrap_servers = [
        "b-2.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092",
        "b-1.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092",
    ]
    assert event.bootstrapServers == bootstrap_servers
    assert (
        event.eventSourceArn
        == "arn:aws:kafka:us-east-1:0123456789019:cluster/SalesCluster/abcd1234-abcd-cafe-abab-9876543210ab-4"
    )

    records = list(event.records["mytopic-0"])
    assert len(records) == 1
    record: KafkaRecordModel = records[0]
    assert record.topic == "mytopic"
    assert record.partition == 0
    assert record.offset == 15
    assert record.timestamp is not None
    convert_time = int(round(record.timestamp.timestamp() * 1000))
    assert convert_time == 1545084650987
    assert record.timestampType == "CREATE_TIME"
    assert record.key == b"recordKey"
    assert record.value == '{"key":"value"}'
    assert len(record.headers) == 1
    assert record.headers[0]["headerKey"] == b"headerValue"
