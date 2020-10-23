import json
from typing import Dict, Union

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, event_parser, exceptions
from aws_lambda_powertools.utilities.typing import LambdaContext


@pytest.mark.parametrize("invalid_value", [None, bool(), [], (), object])
def test_parser_unsupported_event(dummy_schema, invalid_value):
    @event_parser(model=dummy_schema)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    with pytest.raises(ValidationError):
        handle_no_envelope(event=invalid_value, context=LambdaContext())


@pytest.mark.parametrize(
    "invalid_envelope,expected", [(True, ""), (["dummy"], ""), (object, exceptions.InvalidEnvelopeError)]
)
def test_parser_invalid_envelope_type(dummy_event, dummy_schema, invalid_envelope, expected):
    @event_parser(model=dummy_schema, envelope=invalid_envelope)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    if hasattr(expected, "__cause__"):
        with pytest.raises(expected):
            handle_no_envelope(event=dummy_event["payload"], context=LambdaContext())
    else:
        handle_no_envelope(event=dummy_event["payload"], context=LambdaContext())


def test_parser_schema_with_envelope(dummy_event, dummy_schema, dummy_envelope):
    @event_parser(model=dummy_schema, envelope=dummy_envelope)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    handle_no_envelope(dummy_event, LambdaContext())


def test_parser_schema_no_envelope(dummy_event, dummy_schema):
    @event_parser(model=dummy_schema)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    handle_no_envelope(dummy_event["payload"], LambdaContext())


@pytest.mark.parametrize("invalid_schema", [None, str, bool(), [], (), object])
def test_parser_with_invalid_schema_type(dummy_event, invalid_schema):
    @event_parser(model=invalid_schema)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    with pytest.raises(exceptions.InvalidModelTypeError):
        handle_no_envelope(event=dummy_event, context=LambdaContext())


def test_parser_event_as_json_string(dummy_event, dummy_schema):
    dummy_event = json.dumps(dummy_event["payload"])

    @event_parser(model=dummy_schema)
    def handle_no_envelope(event: Union[Dict, str], _: LambdaContext):
        return event

    handle_no_envelope(dummy_event, LambdaContext())
