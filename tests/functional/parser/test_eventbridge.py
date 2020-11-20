from typing import Any

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyAdvancedEventbridgeBusiness, MyEventbridgeBusiness
from tests.functional.parser.utils import load_event


@event_parser(model=MyEventbridgeBusiness, envelope=envelopes.EventBridgeEnvelope)
def handle_eventbridge(event: MyEventbridgeBusiness, _: LambdaContext):
    assert event.instance_id == "i-1234567890abcdef0"
    assert event.state == "terminated"


@event_parser(model=MyAdvancedEventbridgeBusiness)
def handle_eventbridge_no_envelope(event: MyAdvancedEventbridgeBusiness, _: LambdaContext):
    assert event.detail.instance_id == "i-1234567890abcdef0"
    assert event.detail.state == "terminated"
    assert event.id == "6a7e8feb-b491-4cf7-a9f1-bf3703467718"
    assert event.version == "0"
    assert event.account == "111122223333"
    time_str = event.time.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert time_str == "2017-12-22T18:43:48Z"
    assert event.region == "us-west-1"
    assert event.resources == ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"]
    assert event.source == "aws.ec2"
    assert event.detail_type == "EC2 Instance State-change Notification"
    assert event.replay_name == "replay_archive"


def test_handle_eventbridge_trigger_event():
    event_dict = load_event("eventBridgeEvent.json")
    handle_eventbridge(event_dict, LambdaContext())


def test_validate_event_does_not_conform_with_user_dict_model():
    event_dict: Any = {
        "version": "0",
        "id": "6a7e8feb-b491-4cf7-a9f1-bf3703467718",
        "detail-type": "EC2 Instance State-change Notification",
        "source": "aws.ec2",
        "account": "111122223333",
        "time": "2017-12-22T18:43:48Z",
        "region": "us-west-1",
        "resources": ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
        "detail": {},
    }
    with pytest.raises(ValidationError) as e:
        handle_eventbridge(event_dict, LambdaContext())
    print(e.exconly())


def test_handle_eventbridge_trigger_event_no_envelope():
    event_dict = load_event("eventBridgeEvent.json")
    handle_eventbridge_no_envelope(event_dict, LambdaContext())


def test_handle_invalid_event_with_eventbridge_envelope():
    with pytest.raises(ValidationError):
        handle_eventbridge(event={}, context=LambdaContext())
