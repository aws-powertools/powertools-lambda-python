import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, parse
from tests.functional.utils import load_event
from tests.unit.parser.schemas import (
    MyAdvancedEventbridgeBusiness,
    MyEventbridgeBusiness,
)


def test_handle_eventbridge_trigger_event():
    raw_event = load_event("eventBridgeEvent.json")
    parsed_event: MyEventbridgeBusiness = parse(
        event=raw_event,
        model=MyEventbridgeBusiness,
        envelope=envelopes.EventBridgeEnvelope,
    )

    assert parsed_event.instance_id == raw_event["detail"]["instance_id"]
    assert parsed_event.state == raw_event["detail"]["state"]


def test_validate_event_does_not_conform_with_user_dict_model():
    raw_event = load_event("eventBridgeEvent.json")

    raw_event.pop("version")

    with pytest.raises(ValidationError):
        parse(event=raw_event, model=MyEventbridgeBusiness, envelope=envelopes.EventBridgeEnvelope)


def test_handle_eventbridge_trigger_event_no_envelope():
    raw_event = load_event("eventBridgeEvent.json")
    parsed_event: MyAdvancedEventbridgeBusiness = MyAdvancedEventbridgeBusiness(**raw_event)

    assert parsed_event.detail.instance_id == raw_event["detail"]["instance_id"]
    assert parsed_event.detail.state == raw_event["detail"]["state"]
    assert parsed_event.id == raw_event["id"]
    assert parsed_event.version == raw_event["version"]
    assert parsed_event.account == raw_event["account"]
    time_str = parsed_event.time.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert time_str == raw_event["time"]
    assert parsed_event.region == raw_event["region"]
    assert parsed_event.resources == raw_event["resources"]
    assert parsed_event.source == raw_event["source"]
    assert parsed_event.detail_type == raw_event["detail-type"]
    assert parsed_event.replay_name == raw_event["replay-name"]


def test_handle_invalid_event_with_eventbridge_envelope():
    empty_event = {}
    with pytest.raises(ValidationError):
        parse(event=empty_event, model=MyEventbridgeBusiness, envelope=envelopes.EventBridgeEnvelope)
