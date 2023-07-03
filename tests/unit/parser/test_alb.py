import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, event_parser
from aws_lambda_powertools.utilities.parser.models import AlbModel
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.utils import load_event


@event_parser(model=AlbModel)
def handle_alb(event: AlbModel, _: LambdaContext):
    return event


def test_alb_trigger_event():
    raw_event = load_event("albEvent.json")
    parsed_event: AlbModel = handle_alb(raw_event, LambdaContext())

    assert parsed_event.requestContext.elb.targetGroupArn == raw_event["requestContext"]["elb"]["targetGroupArn"]
    assert parsed_event.httpMethod == raw_event["httpMethod"]
    assert parsed_event.path == raw_event["path"]
    assert parsed_event.queryStringParameters == raw_event["queryStringParameters"]
    assert parsed_event.headers == raw_event["headers"]
    assert parsed_event.body == raw_event["body"]
    assert not parsed_event.isBase64Encoded


def test_validate_event_does_not_conform_with_model():
    event = {"invalid": "event"}
    with pytest.raises(ValidationError):
        handle_alb(event, LambdaContext())
