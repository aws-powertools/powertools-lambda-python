from aws_lambda_powertools.utilities.data_classes import KafkaEvent
from tests.functional.utils import load_event


def test_kafka_msk_event():
    event = KafkaEvent(load_event("kafkaEventMsk.json"))
    assert event.event_source == "aws:kafka"
    assert (
        event.event_source_arn
        == "arn:aws:kafka:us-east-1:0123456789019:cluster/SalesCluster/abcd1234-abcd-cafe-abab-9876543210ab-4"
    )

    bootstrap_servers_raw = "b-2.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092,b-1.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092"  # noqa E501

    bootstrap_servers_list = [
        "b-2.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092",
        "b-1.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092",
    ]

    assert event.bootstrap_servers == bootstrap_servers_raw
    assert event.decoded_bootstrap_servers == bootstrap_servers_list

    records = list(event.records)
    assert len(records) == 1
    record = records[0]
    assert record.topic == "mytopic"
    assert record.partition == 0
    assert record.offset == 15
    assert record.timestamp == 1545084650987
    assert record.timestamp_type == "CREATE_TIME"
    assert record.decoded_key == b"recordKey"
    assert record.value == "eyJrZXkiOiJ2YWx1ZSJ9"
    assert record.json_value == {"key": "value"}
    assert record.decoded_headers == {"headerKey": b"headerValue"}
    assert record.get_header_value("HeaderKey", case_sensitive=False) == b"headerValue"


def test_kafka_self_managed_event():
    event = KafkaEvent(load_event("kafkaEventSelfManaged.json"))
    assert event.event_source == "aws:SelfManagedKafka"

    bootstrap_servers_raw = "b-2.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092,b-1.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092"  # noqa E501

    bootstrap_servers_list = [
        "b-2.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092",
        "b-1.demo-cluster-1.a1bcde.c1.kafka.us-east-1.amazonaws.com:9092",
    ]

    assert event.bootstrap_servers == bootstrap_servers_raw
    assert event.decoded_bootstrap_servers == bootstrap_servers_list

    records = list(event.records)
    assert len(records) == 1
    record = records[0]
    assert record.topic == "mytopic"
    assert record.partition == 0
    assert record.offset == 15
    assert record.timestamp == 1545084650987
    assert record.timestamp_type == "CREATE_TIME"
    assert record.decoded_key == b"recordKey"
    assert record.value == "eyJrZXkiOiJ2YWx1ZSJ9"
    assert record.json_value == {"key": "value"}
    assert record.decoded_headers == {"headerKey": b"headerValue"}
    assert record.get_header_value("HeaderKey", case_sensitive=False) == b"headerValue"
