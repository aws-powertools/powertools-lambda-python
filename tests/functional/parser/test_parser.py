from typing import Dict

import pytest

from aws_lambda_powertools.utilities.parser import exceptions, parser
from aws_lambda_powertools.utilities.typing import LambdaContext


@pytest.mark.parametrize("invalid_value", [None, bool(), [], (), object])
def test_parser_unsupported_event(dummy_schema, invalid_value):
    @parser(schema=dummy_schema)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    with pytest.raises(exceptions.SchemaValidationError):
        handle_no_envelope(event=invalid_value, context=LambdaContext())


@pytest.mark.parametrize("invalid_envelope", [True, ["dummy"], ("dummy"), object])
def test_parser_invalid_envelope_type(dummy_event, dummy_schema, invalid_envelope):
    @parser(schema=dummy_schema, envelope=invalid_envelope)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    with pytest.raises(exceptions.InvalidEnvelopeError):
        handle_no_envelope(event=dummy_event["payload"], context=LambdaContext())


def test_parser_schema_with_envelope(dummy_event, dummy_schema, dummy_envelope):
    @parser(schema=dummy_schema, envelope=dummy_envelope)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    handle_no_envelope(dummy_event, LambdaContext())


def test_parser_schema_no_envelope(dummy_event, dummy_schema):
    @parser(schema=dummy_schema)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    handle_no_envelope(dummy_event["payload"], LambdaContext())


@pytest.mark.parametrize("invalid_schema", [None, str, bool(), [], (), object])
def test_parser_with_invalid_schema_type(dummy_event, invalid_schema):
    @parser(schema=invalid_schema)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    with pytest.raises(exceptions.InvalidSchemaTypeError):
        handle_no_envelope(event=dummy_event, context=LambdaContext())
