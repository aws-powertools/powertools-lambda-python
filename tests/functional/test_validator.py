import io
from http import HTTPStatus
from typing import Any, Dict, Optional

import pytest
from aws_lambda_context import LambdaContext
from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from aws_lambda_powertools.validation.validator import DynamoDBEnvelope, EventBridgeEnvelope, UserEnvelope, validator


class OutboundSchema(BaseModel):
    response_code: HTTPStatus
    message: str


class InboundSchema(BaseModel):
    greeting: str


@pytest.fixture
def stdout():
    return io.StringIO()


@validator(inbound_schema_model=InboundSchema, outbound_schema_model=OutboundSchema, envelope=UserEnvelope())
def my_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Optional[Any]]:
    assert event["custom"]
    assert event["orig"]
    return {"response_code": 200, "message": "working"}


@validator(inbound_schema_model=InboundSchema, outbound_schema_model=OutboundSchema, envelope=UserEnvelope())
def my_outbound_fail_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Optional[Any]]:
    assert event["custom"]
    assert event["orig"]
    return {"stuff": 200, "message": "working"}


def test_ok_inbound_outbound_validation():
    my_handler({"greeting": "hello"}, LambdaContext())


def test_fail_outbound():
    with pytest.raises(ValidationError):
        my_outbound_fail_handler({"greeting": "hello"}, LambdaContext())


def test_fail_inbound_validation():
    with pytest.raises(ValidationError):
        my_handler({"this_fails": "hello"}, LambdaContext())


class MyMessage(BaseModel):
    message: str
    messageId: int


@validator(inbound_schema_model=MyMessage, outbound_schema_model=OutboundSchema, envelope=DynamoDBEnvelope())
def dynamodb_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Optional[Any]]:
    assert event["custom"]
    #  first record
    assert not event["custom"][0]["old"]
    assert event["custom"][0]["new"].message == "hello"
    assert event["custom"][0]["new"].messageId == 8
    #  second record
    assert event["custom"][1]["new"].message == "new_hello"
    assert event["custom"][1]["new"].messageId == 88
    assert event["custom"][1]["old"].message == "hello"
    assert event["custom"][1]["old"].messageId == 81
    #  third record
    assert not event["custom"][2]["new"]
    assert event["custom"][2]["old"].message == "hello1"
    assert event["custom"][2]["old"].messageId == 82
    assert event["orig"]

    return {"response_code": 200, "message": "working"}


def test_dynamodb_fail_inbound_validation():
    event = {"greeting": "hello"}
    with pytest.raises(ValidationError):
        dynamodb_handler(event, LambdaContext())


def test_dynamodb_ok_inbound_outbound_validation():
    event = {
        "Records": [
            {
                "eventID": "8ae66d82798e8c34ca4a568d6d2ddb75",
                "eventName": "INSERT",
                "eventVersion": "1.1",
                "eventSource": "aws:dynamodb",
                "awsRegion": "eu-west-1",
                "dynamodb": {
                    "ApproximateCreationDateTime": 1583747504.0,
                    "Keys": {"id": {"S": "a5890cc9-47c7-4667-928b-f072b93f7acd"}},
                    "NewImage": {"message": "hello", "messageId": 8},
                    "SequenceNumber": "4722000000000004992628049",
                    "SizeBytes": 215,
                    "StreamViewType": "NEW_AND_OLD_IMAGES",
                },
                "eventSourceARN": "arn:aws:dynamodb/stream/2020-0",
            },
            {
                "eventID": "8ae66d82798e83333568d6d2ddb75",
                "eventName": "MODIFY",
                "eventVersion": "1.1",
                "eventSource": "aws:dynamodb",
                "awsRegion": "eu-west-1",
                "dynamodb": {
                    "ApproximateCreationDateTime": 1583747504.0,
                    "Keys": {"id": {"S": "a5890cc9-47c7-4667-928b-f072b93f7acd"}},
                    "NewImage": {"message": "new_hello", "messageId": 88},
                    "OldImage": {"message": "hello", "messageId": 81},
                    "SequenceNumber": "4722000000000004992628049",
                    "SizeBytes": 215,
                    "StreamViewType": "NEW_AND_OLD_IMAGES",
                },
                "eventSourceARN": "arn:aws:dynamodb/stream/2020-0",
            },
            {
                "eventID": "8ae66d82798e8c34ca4a568d6d2ddb75",
                "eventName": "REMOVE",
                "eventVersion": "1.1",
                "eventSource": "aws:dynamodb",
                "awsRegion": "eu-west-1",
                "dynamodb": {
                    "ApproximateCreationDateTime": 1583747504.0,
                    "Keys": {"id": {"S": "a5890cc9-47c7-4667-928b-f072b93f7acd"}},
                    "OldImage": {"message": "hello1", "messageId": 82},
                    "SequenceNumber": "4722000000000004992628049",
                    "SizeBytes": 215,
                    "StreamViewType": "NEW_AND_OLD_IMAGES",
                },
                "eventSourceARN": "arn:aws:dynamodb/stream/2020-0",
            },
        ]
    }
    dynamodb_handler(event, LambdaContext())


@validator(inbound_schema_model=MyMessage, outbound_schema_model=OutboundSchema, envelope=EventBridgeEnvelope())
def eventbridge_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Optional[Any]]:
    assert event["custom"]
    assert event["custom"].messageId == 8
    assert event["custom"].message == "hello"
    assert event["orig"]
    return {"response_code": 200, "message": "working"}


def test_eventbridge_ok_validation():
    event = {
        "version": "0",
        "id": "553961c5-5017-5763-6f21-f88d5f5f4b05",
        "detail-type": "my func stream event json",
        "source": "arn:aws:lambda:eu-west-1:88888888:function:my_func",
        "account": "88888888",
        "time": "2020-02-11T08:18:09Z",
        "region": "eu-west-1",
        "resources": ["arn:aws:dynamodb:eu-west-1:88888888:table/stream/2020-02"],
        "detail": {"message": "hello", "messageId": 8},
    }
    eventbridge_handler(event, LambdaContext())


def test_eventbridge_fail_inbound_validation():
    event = {"greeting": "hello"}
    with pytest.raises(ValidationError):
        eventbridge_handler(event, LambdaContext())
