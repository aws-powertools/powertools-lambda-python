from aws_lambda_powertools.utilities.advanced_parser.envelopes.envelopes import Envelope
from aws_lambda_powertools.utilities.advanced_parser.parser import parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyAdvancedEventbridgeBusiness, MyEventbridgeBusiness
from tests.functional.parser.utils import load_event


@parser(schema=MyEventbridgeBusiness, envelope=Envelope.EVENTBRIDGE)
def handle_eventbridge(event: MyEventbridgeBusiness, context: LambdaContext):
    assert event.instance_id == "i-1234567890abcdef0"
    assert event.state == "terminated"


@parser(schema=MyAdvancedEventbridgeBusiness)
def handle_eventbridge_no_envelope(event: MyAdvancedEventbridgeBusiness, context: LambdaContext):
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
    assert event.detailtype == "EC2 Instance State-change Notification"


def test_handle_eventbridge_trigger_event():
    event_dict = load_event("eventBridgeEvent.json")
    handle_eventbridge(event_dict, LambdaContext())


def test_handle_eventbridge_trigger_event_no_envelope():
    event_dict = load_event("eventBridgeEvent.json")
    handle_eventbridge_no_envelope(event_dict, LambdaContext())
