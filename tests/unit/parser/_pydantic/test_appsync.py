from aws_lambda_powertools.utilities.parser import parse, ValidationError
from aws_lambda_powertools.utilities.parser.models import AppSyncResolverEventModel
from tests.functional.utils import load_event


def test_appsync_event_model_parses_successfully():
    """
    Validate that a valid AppSync resolver event is correctly parsed by the model.
    """
    event = load_event("appsync_resolver_event.json")
    parsed_event = parse(event=event, model=AppSyncResolverEventModel)

    assert parsed_event.arguments["page"] == 2
    assert parsed_event.identity.username == "mike"
    assert parsed_event.request.headers["host"].endswith("appsync-api.us-east-1.amazonaws.com")
    assert parsed_event.info.fieldName == "locations"
    assert parsed_event.info.parentTypeName == "Merchant"


def test_appsync_event_model_invalid_payload_raises():
    """
    Validate that parsing an invalid AppSync resolver event payload raises a ValidationError.
    """
    invalid_event = {"invalid": "event"}
    with pytest.raises(ValidationError):
        parse(event=invalid_event, model=AppSyncResolverEventModel)