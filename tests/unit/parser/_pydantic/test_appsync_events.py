import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, parse
from aws_lambda_powertools.utilities.parser.models import AppSyncEventsModel
from tests.functional.utils import load_event


def test_appsync_event_model_parses_successfully():
    """
    Validate that a valid AppSync resolver events is correctly parsed by the model.
    """
    event = load_event("appSyncEventsEvent.json")
    parsed_event = parse(event=event, model=AppSyncEventsModel)

    assert isinstance(parsed_event, AppSyncEventsModel)


def test_appsync_event_model_invalid_payload_raises():
    """
    Validate that parsing an invalid AppSync resolver events payload raises a ValidationError.
    """
    invalid_event = {"invalid": "event"}
    with pytest.raises(ValidationError):
        parse(event=invalid_event, model=AppSyncEventsModel)
