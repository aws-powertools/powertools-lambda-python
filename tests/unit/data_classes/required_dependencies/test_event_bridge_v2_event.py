from __future__ import annotations

import base64

from aws_lambda_powertools.utilities.data_classes import EventBridgeV2Event
from tests.functional.utils import load_event


def test_event_bridge_v2_event_with_metadata_array():
    raw_event = load_event("eventBridgeV2Event.json")
    event = EventBridgeV2Event(raw_event)

    raw_record, put_events_record = event.records
    assert len(event.records) == 2

    assert raw_record.data == raw_event[0]["Data"]
    assert raw_record.detail is None
    assert raw_record.metadata == {"sub": "s3", "tenant": "acme"}
    assert raw_record.system_metadata.event_id == "e3474ffa-0283-4fe7-af27-803e30cd92f4"
    assert raw_record.system_metadata.sequence_number == "10000000000000007000"
    assert raw_record.system_metadata.delivery_type == "LIVE"
    assert raw_record.system_metadata.event_group_id == "43e6837b-3d96-44db-863d-e8abd80cd1e8"
    assert raw_record.system_metadata.deduplication_id == "43e6837b-3d96-44db-863d-e8abd80cd1e8"
    assert raw_record.system_metadata.content_type == "application/json"
    assert raw_record.system_metadata.ingestion_time == "2026-10-25T11:48:54.064Z"
    assert raw_record.system_metadata.source is None
    assert raw_record.system_metadata.detail_type is None

    assert put_events_record.detail == {"orderId": "s6-1", "total": 10}
    assert put_events_record.metadata == {}
    assert put_events_record.system_metadata.delivery_type == "REPLAY"
    assert put_events_record.system_metadata.source == "com.example.orders"
    assert put_events_record.system_metadata.detail_type == "s6"


def test_event_bridge_v2_event_single_object():
    raw_event = load_event("eventBridgeV2Event.json")[0]
    event = EventBridgeV2Event(raw_event)

    assert len(event.records) == 1
    assert event.records[0].data == raw_event["Data"]


def test_event_bridge_v2_event_octet_stream():
    payload = b"\x00\x01binary"
    raw_event = {
        "Data": base64.b64encode(payload).decode(),
        "Metadata": {},
        "SystemMetadata": {"ContentType": "application/octet-stream", "aws:EventId": "id"},
    }

    assert EventBridgeV2Event(raw_event).records[0].data == payload


def test_event_bridge_v2_event_raw_classic_envelope_and_array():
    classic = load_event("eventBridgeEvent.json")

    single = EventBridgeV2Event(classic).records
    array = EventBridgeV2Event([classic, classic]).records

    assert len(single) == 1
    assert len(array) == 2
    assert single[0].data == classic
    assert single[0].detail == classic["detail"]
    assert single[0].metadata == {}
    assert single[0].system_metadata.event_id is None


def test_event_bridge_v2_event_raw_put_raw_events_payload():
    event = EventBridgeV2Event({"orderId": "1", "total": 5})

    assert event.records[0].data == {"orderId": "1", "total": 5}
    assert event.records[0].detail is None
