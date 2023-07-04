import pytest

from aws_lambda_powertools.utilities.parser import (
    ValidationError,
    envelopes,
    event_parser,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import (
    MyAdvancedEventbridgeBusiness,
    MyEventbridgeBusiness,
)
from tests.functional.utils import load_event


@event_parser(model=MyEventbridgeBusiness, envelope=envelopes.EventBridgeEnvelope)
def handle_eventbridge(event: MyEventbridgeBusiness, _: LambdaContext):
    return event


@event_parser(model=MyAdvancedEventbridgeBusiness)
def handle_eventbridge_no_envelope(event: MyAdvancedEventbridgeBusiness, _: LambdaContext):
    return event


def test_handle_eventbridge_trigger_event():
    raw_event = load_event("eventBridgeEvent.json")
    parsed_event: MyEventbridgeBusiness = handle_eventbridge(raw_event, LambdaContext())

    assert parsed_event.instance_id == raw_event["detail"]["instance_id"]
    assert parsed_event.state == raw_event["detail"]["state"]


def test_validate_event_does_not_conform_with_user_dict_model():
    raw_event = load_event("eventBridgeEvent.json")

    raw_event.pop("version")

    with pytest.raises(ValidationError):
        handle_eventbridge(raw_event, LambdaContext())


def test_handle_eventbridge_trigger_event_no_envelope():
    raw_event = load_event("eventBridgeEvent.json")
    parsed_event: MyAdvancedEventbridgeBusiness = handle_eventbridge_no_envelope(raw_event, LambdaContext())

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
    with pytest.raises(ValidationError):
        handle_eventbridge(event={}, context=LambdaContext())
