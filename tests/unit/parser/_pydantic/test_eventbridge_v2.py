import base64

import pytest
from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, parse
from aws_lambda_powertools.utilities.parser.models import EventBridgeV2Model
from tests.functional.utils import load_event


class Order(BaseModel):
    orderId: str  # noqa: N815
    total: int


def test_model_accepts_array_and_single():
    raw_event = load_event("eventBridgeV2Event.json")

    from_array = EventBridgeV2Model.model_validate(raw_event).root
    from_single = EventBridgeV2Model.model_validate(raw_event[0]).root

    assert len(from_array) == 2
    assert len(from_single) == 1
    assert from_array[0].metadata == {"sub": "s3", "tenant": "acme"}
    assert from_array[0].system_metadata.event_id == "e3474ffa-0283-4fe7-af27-803e30cd92f4"
    assert from_array[0].system_metadata.delivery_type == "LIVE"
    assert from_array[1].system_metadata.delivery_type == "REPLAY"
    assert from_array[1].system_metadata.detail_type == "s6"


def test_model_decodes_octet_stream():
    raw_event = {
        "Data": base64.b64encode(b"abc").decode(),
        "Metadata": {},
        "SystemMetadata": {
            "ContentType": "application/octet-stream",
            "aws:EventId": "id",
            "aws:SequenceNumber": "1",
            "aws:DeliveryType": "LIVE",
            "aws:IngestionTime": "2026-10-25T11:48:54.064Z",
        },
    }

    assert EventBridgeV2Model.model_validate(raw_event).root[0].data == b"abc"


def test_model_rejects_invalid_delivery_type():
    raw_event = load_event("eventBridgeV2Event.json")[0]
    raw_event["SystemMetadata"]["aws:DeliveryType"] = "OTHER"

    with pytest.raises(ValidationError):
        EventBridgeV2Model.model_validate(raw_event)


def test_envelope_with_metadata_array_yields_data_and_detail():
    raw_event = load_event("eventBridgeV2Event.json")

    parsed = parse(event=raw_event, model=Order, envelope=envelopes.EventBridgeV2Envelope)

    assert parsed == [Order(orderId="s3-0", total=5), Order(orderId="s6-1", total=10)]


def test_envelope_with_metadata_single_object():
    raw_event = load_event("eventBridgeV2Event.json")[0]

    parsed = parse(event=raw_event, model=Order, envelope=envelopes.EventBridgeV2Envelope)

    assert parsed == [Order(orderId="s3-0", total=5)]


def test_envelope_raw_deliveries():
    classic = load_event("eventBridgeEvent.json")
    classic["detail"] = {"orderId": "c", "total": 1}

    assert parse(event=classic, model=Order, envelope=envelopes.EventBridgeV2Envelope) == [Order(orderId="c", total=1)]
    assert parse(event=[classic], model=Order, envelope=envelopes.EventBridgeV2Envelope) == [
        Order(orderId="c", total=1),
    ]
    assert parse(event={"orderId": "b", "total": 2}, model=Order, envelope=envelopes.EventBridgeV2Envelope) == [
        Order(orderId="b", total=2),
    ]


def test_envelope_invalid_payload():
    raw_event = load_event("eventBridgeV2Event.json")
    raw_event[0]["Data"] = {"orderId": "x"}

    with pytest.raises(ValidationError):
        parse(event=raw_event, model=Order, envelope=envelopes.EventBridgeV2Envelope)


def test_envelope_parses_octet_stream_json_bytes():
    # GIVEN a JSON payload published as application/octet-stream, which the bus delivers base64 encoded
    event = {
        "Data": base64.b64encode(b'{"orderId": "o-1", "total": 5}').decode(),
        "Metadata": {},
        "SystemMetadata": {"ContentType": "application/octet-stream", "aws:DeliveryType": "LIVE"},
    }

    # WHEN parsing with the envelope
    orders = parse(event=event, model=Order, envelope=envelopes.EventBridgeV2Envelope)

    # THEN the bytes are decoded and parsed into the model, and the optional aws: fields may be absent
    assert orders == [Order(orderId="o-1", total=5)]
