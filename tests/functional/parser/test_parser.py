import json
from datetime import datetime
from typing import Any, Dict, Literal, Union

import pydantic
import pytest
from pydantic import BaseModel, ValidationError
from typing_extensions import Annotated

from aws_lambda_powertools.utilities.parser import event_parser, exceptions, parse
from aws_lambda_powertools.utilities.parser.envelopes.sqs import SqsEnvelope
from aws_lambda_powertools.utilities.parser.models import SqsModel
from aws_lambda_powertools.utilities.parser.models.event_bridge import EventBridgeModel
from aws_lambda_powertools.utilities.typing import LambdaContext


@pytest.mark.parametrize("invalid_value", [None, False, [], (), object])
def test_parser_unsupported_event(dummy_schema, invalid_value):
    @event_parser(model=dummy_schema)
    def handle_no_envelope(event: Dict, _: LambdaContext):
        return event

    with pytest.raises(ValidationError):
        handle_no_envelope(event=invalid_value, context=LambdaContext())


@pytest.mark.parametrize(
    "invalid_envelope,expected",
    [(True, ""), (["dummy"], ""), (object, exceptions.InvalidEnvelopeError)],
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


@pytest.mark.usefixtures("pydanticv2_only")
def test_pydanticv2_validation():
    class FakeModel(pydantic.BaseModel):
        region: str
        event_name: str
        version: int

        # WHEN using the validator for v2
        @pydantic.field_validator("version", mode="before")
        def validate_field(cls, value):
            return int(value)

    event_raw = {"region": "us-east-1", "event_name": "aws-powertools", "version": "10"}
    event_parsed = FakeModel(**event_raw)

    # THEN parse the event as expected
    assert event_parsed.region == event_raw["region"]
    assert event_parsed.event_name == event_raw["event_name"]
    assert event_parsed.version == int(event_raw["version"])


@pytest.mark.parametrize("invalid_schema", [False, [], ()])
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


def test_parser_event_with_type_hint(dummy_event, dummy_schema):
    @event_parser
    def handler(event: dummy_schema, _: LambdaContext):
        assert event.message == "hello world"

    handler(dummy_event["payload"], LambdaContext())


def test_parser_event_without_type_hint(dummy_event, dummy_schema):
    @event_parser
    def handler(event, _):
        assert event.message == "hello world"

    with pytest.raises(exceptions.InvalidModelTypeError):
        handler(dummy_event["payload"], LambdaContext())


def test_parser_event_with_type_hint_and_non_default_argument(dummy_event, dummy_schema):
    @event_parser
    def handler(evt: dummy_schema, _: LambdaContext):
        assert evt.message == "hello world"

    handler(dummy_event["payload"], LambdaContext())


def test_parser_event_with_payload_not_match_schema(dummy_event, dummy_schema):
    @event_parser(model=dummy_schema)
    def handler(event, _):
        assert event.message == "hello world"

    with pytest.raises(ValidationError):
        handler({"project": "powertools"}, LambdaContext())


def test_parser_validation_error():
    class StrictModel(pydantic.BaseModel):
        age: int
        name: str

    @event_parser(model=StrictModel)
    def handle_validation(event: Dict, _: LambdaContext):
        return event

    invalid_event = {"age": "not_a_number", "name": 123}  # intentionally wrong types

    with pytest.raises(ValidationError) as exc_info:
        handle_validation(event=invalid_event, context=LambdaContext())

    assert "age" in str(exc_info.value)  # Verify the error mentions the invalid field


def test_parser_type_value_errors():
    class CustomModel(pydantic.BaseModel):
        timestamp: datetime
        status: Literal["SUCCESS", "FAILURE"]

    @event_parser(model=CustomModel)
    def handle_type_validation(event: Dict, _: LambdaContext):
        return event

    # Test both TypeError and ValueError scenarios
    invalid_events = [
        {"timestamp": "invalid-date", "status": "SUCCESS"},  # Will raise ValueError for invalid date
        {"timestamp": datetime.now(), "status": "INVALID"},  # Will raise ValueError for invalid literal
    ]

    for invalid_event in invalid_events:
        with pytest.raises((TypeError, ValueError)):
            handle_type_validation(event=invalid_event, context=LambdaContext())


def test_event_parser_no_model():
    with pytest.raises(exceptions.InvalidModelTypeError):

        @event_parser
        def handler(event, _):
            return event

        handler({}, None)


class Shopping(BaseModel):
    id: int
    description: str


def test_event_parser_invalid_event():
    event = {"id": "forgot-the-id", "description": "really nice blouse"}  # 'id' is invalid

    @event_parser(model=Shopping)
    def handler(event, _):
        return event

    with pytest.raises(ValidationError):
        handler(event, None)

    with pytest.raises(ValidationError):
        parse(event, model=Shopping)


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            {"status": "succeeded", "name": "Clifford", "breed": "Labrador"},
            "Successfully retrieved Labrador named Clifford",
        ),
        (
            {"status": "failed", "error": "oh some error"},
            "Uh oh. Had a problem: oh some error",
        ),
    ],
)
def test_parser_unions(test_input, expected):
    class SuccessfulCallback(pydantic.BaseModel):
        status: Literal["succeeded"]
        name: str
        breed: Literal["Newfoundland", "Labrador"]

    class FailedCallback(pydantic.BaseModel):
        status: Literal["failed"]
        error: str

    DogCallback = Annotated[Union[SuccessfulCallback, FailedCallback], pydantic.Field(discriminator="status")]

    @event_parser(model=DogCallback)
    def handler(event, _: Any) -> str:
        if isinstance(event, FailedCallback):
            return f"Uh oh. Had a problem: {event.error}"

        return f"Successfully retrieved {event.breed} named {event.name}"

    ret = handler(test_input, None)
    assert ret == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            {"status": "succeeded", "name": "Clifford", "breed": "Labrador"},
            "Successfully retrieved Labrador named Clifford",
        ),
        (
            {"status": "failed", "error": "oh some error"},
            "Uh oh. Had a problem: oh some error",
        ),
    ],
)
def test_parser_unions_with_type_adapter_instance(test_input, expected):
    class SuccessfulCallback(pydantic.BaseModel):
        status: Literal["succeeded"]
        name: str
        breed: Literal["Newfoundland", "Labrador"]

    class FailedCallback(pydantic.BaseModel):
        status: Literal["failed"]
        error: str

    DogCallback = Annotated[Union[SuccessfulCallback, FailedCallback], pydantic.Field(discriminator="status")]
    DogCallbackTypeAdapter = pydantic.TypeAdapter(DogCallback)

    @event_parser(model=DogCallbackTypeAdapter)
    def handler(event, _: Any) -> str:
        if isinstance(event, FailedCallback):
            return f"Uh oh. Had a problem: {event.error}"

        return f"Successfully retrieved {event.breed} named {event.name}"

    ret = handler(test_input, None)
    assert ret == expected


def test_parser_with_model_type_model_and_envelope():
    event = {
        "Records": [
            {
                "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
                "receiptHandle": "MessageReceiptHandle",
                "body": EventBridgeModel(
                    version="version",
                    id="id",
                    source="source",
                    account="account",
                    time=datetime.now(),
                    detail_type="MyEvent",
                    region="region",
                    resources=[],
                    detail={"key": "value"},
                ).model_dump_json(),
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1523232000000",
                    "SenderId": "123456789012",
                    "ApproximateFirstReceiveTimestamp": "1523232000001",
                },
                "messageAttributes": {},
                "md5OfBody": "{{{md5_of_body}}}",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
                "awsRegion": "us-east-1",
            },
        ],
    }

    def handler(event: SqsModel, _: LambdaContext):
        parsed_event: EventBridgeModel = parse(event, model=EventBridgeModel, envelope=SqsEnvelope)
        print(parsed_event)
        assert parsed_event[0].version == "version"

    handler(event, LambdaContext())
