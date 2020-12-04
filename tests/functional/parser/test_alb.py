import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, event_parser
from aws_lambda_powertools.utilities.parser.models import AlbModel
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.utils import load_event


@event_parser(model=AlbModel)
def handle_alb(event: AlbModel, _: LambdaContext):
    assert (
        event.requestContext.elb.targetGroupArn
        == "arn:aws:elasticloadbalancing:us-east-2:123456789012:targetgroup/lambda-279XGJDqGZ5rsrHC2Fjr/49e9d65c45c6791a"  # noqa E501
    )
    assert event.httpMethod == "GET"
    assert event.path == "/lambda"
    assert event.queryStringParameters == {"query": "1234ABCD"}
    assert event.headers == {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "accept-encoding": "gzip",
        "accept-language": "en-US,en;q=0.9",
        "connection": "keep-alive",
        "host": "lambda-alb-123578498.us-east-2.elb.amazonaws.com",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",  # noqa E501
        "x-amzn-trace-id": "Root=1-5c536348-3d683b8b04734faae651f476",
        "x-forwarded-for": "72.12.164.125",
        "x-forwarded-port": "80",
        "x-forwarded-proto": "http",
        "x-imforwards": "20",
    }
    assert event.body == "Test"
    assert not event.isBase64Encoded


def test_alb_trigger_event():
    event_dict = load_event("albEvent.json")
    handle_alb(event_dict, LambdaContext())


def test_validate_event_does_not_conform_with_model():
    event = {"invalid": "event"}
    with pytest.raises(ValidationError):
        handle_alb(event, LambdaContext())
