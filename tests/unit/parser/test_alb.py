import pytest

from aws_lambda_powertools.utilities.parser import ValidationError
from aws_lambda_powertools.utilities.parser.models import AlbModel
from tests.functional.utils import load_event


def test_alb_trigger_event():
    raw_event = load_event("albEvent.json")
    parsed_event: AlbModel = AlbModel(**raw_event)

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
        AlbModel(**event)
