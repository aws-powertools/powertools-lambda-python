from http import HTTPStatus
from typing import Any, Dict, Optional

import pytest
from aws_lambda_context import LambdaContext
from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from aws_lambda_powertools.utilities.validation import (
    DynamoDBEnvelope,
    EventBridgeEnvelope,
    SqsEnvelope,
    UserEnvelope,
    validate,
    validator,
)


class MyMessage(BaseModel):
    message: str
    messageId: int


def test_validate_function():
    eventbridge_event = {
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
    parsed_event = validate(eventbridge_event, MyMessage, EventBridgeEnvelope(), True)
    assert parsed_event.dict() == {"message": "hello", "messageId": 8}


def test_validate_function_no_return_value():
    eventbridge_event = {
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
    parsed_event = validate(eventbridge_event, MyMessage, EventBridgeEnvelope())
    assert parsed_event is None


def test_validate_function_fail_envelope():
    eventbridge_event = {
        "version": "0",
        "id": "553961c5-5017-5763-6f21-f88d5f5f4b05",
        "detail-type": "my func stream event json",
        "source": "arn:aws:lambda:eu-west-1:88888888:function:my_func",
        "time": "2020-02-11T08:18:09Z",
        "region": "eu-west-1",
        "resources": ["arn:aws:dynamodb:eu-west-1:88888888:table/stream/2020-02"],
        "detail": {"message": "hello", "messageId": 8},
    }
    with pytest.raises(ValidationError):
        validate(eventbridge_event, MyMessage, EventBridgeEnvelope())


def test_validate_function_fail_user_schema():
    eventbridge_event = {
        "version": "0",
        "id": "553961c5-5017-5763-6f21-f88d5f5f4b05",
        "detail-type": "my func stream event json",
        "source": "arn:aws:lambda:eu-west-1:88888888:function:my_func",
        "account": "88888888",
        "time": "2020-02-11T08:18:09Z",
        "region": "eu-west-1",
        "resources": ["arn:aws:dynamodb:eu-west-1:88888888:table/stream/2020-02"],
        "detail": {"mess11age": "hello", "messageId": 8},
    }
    with pytest.raises(ValidationError):
        validate(eventbridge_event, MyMessage, EventBridgeEnvelope())


class OutboundSchema(BaseModel):
    response_code: HTTPStatus
    message: str


class InboundSchema(BaseModel):
    greeting: str


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


@validator(inbound_schema_model=MyMessage, outbound_schema_model=OutboundSchema, envelope=DynamoDBEnvelope())
def dynamodb_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Optional[Any]]:
    assert event["custom"]
    assert len(event["custom"]) == 3
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


sqs_event_attribs = {
    "test4": {
        "stringValue": "dfgdfgfd",
        "stringListValues": [],
        "binaryListValues": [],
        "dataType": "String.custom_type",
    },
    "test5": {"stringValue": "a,b,c,d", "stringListValues": [], "binaryListValues": [], "dataType": "String"},
    "tes6": {"stringValue": "112.1", "stringListValues": [], "binaryListValues": [], "dataType": "Number.mytype"},
    "test2": {"stringValue": "111", "stringListValues": [], "binaryListValues": [], "dataType": "Number"},
    "test3": {"binaryValue": "w5NNNcOXXXU=", "stringListValues": [], "binaryListValues": [], "dataType": "Binary"},
    "test": {"stringValue": "gfgf", "stringListValues": [], "binaryListValues": [], "dataType": "String"},
}


@validator(inbound_schema_model=MyMessage, outbound_schema_model=OutboundSchema, envelope=SqsEnvelope())
def sqs_json_body_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Optional[Any]]:
    assert event["custom"]
    assert len(event["custom"]) == 1
    assert event["orig"]
    assert event["custom"][0]["body"].message == "hello"
    assert event["custom"][0]["body"].messageId == 8
    assert len(event["custom"][0]["attributes"]) == len(sqs_event_attribs)
    return {"response_code": 200, "message": "working"}


def test_sqs_ok_json_string_body_validation():
    event = {
        "Records": [
            {
                "messageId": "1743e893-cc24-1234-88f8-f80c37dcd923",
                "receiptHandle": "AKhXK7azPaZHY0zjmTsdfsdfdsfOgcVob",
                "body": '{"message": "hello", "messageId": 8}',
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1598117108660",
                    "SenderId": "43434dsdfd:sdfds",
                    "ApproximateFirstReceiveTimestamp": "1598117108667",
                },
                "messageAttributes": sqs_event_attribs,
                "md5OfBody": "4db76498a982d84c188927c585076a6c",
                "md5OfMessageAttributes": "7186428dc148b402947274e0bb41e7ee",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:mytest",
                "awsRegion": "us-west-1",
            }
        ]
    }
    sqs_json_body_handler(event, LambdaContext())


@validator(inbound_schema_model=str, outbound_schema_model=OutboundSchema, envelope=SqsEnvelope())
def sqs_string_body_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Optional[Any]]:
    assert event["custom"]
    assert len(event["custom"]) == 1
    assert event["orig"]
    assert event["custom"][0]["body"] == "hello how are you"
    assert len(event["custom"][0]["attributes"]) == len(sqs_event_attribs)
    return {"response_code": 200, "message": "working"}


def test_sqs_ok_json_string_validation():
    event = {
        "Records": [
            {
                "messageId": "1743e893-cc24-1234-88f8-f80c37dcd923",
                "receiptHandle": "AKhXK7azPaZHY0zjmTsdfsdfdsfOgcVob",
                "body": "hello how are you",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1598117108660",
                    "SenderId": "43434dsdfd:sdfds",
                    "ApproximateFirstReceiveTimestamp": "1598117108667",
                },
                "messageAttributes": sqs_event_attribs,
                "md5OfBody": "4db76498a982d84c188927c585076a6c",
                "md5OfMessageAttributes": "7186428dc148b402947274e0bb41e7ee",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:mytest",
                "awsRegion": "us-west-1",
            }
        ]
    }
    sqs_string_body_handler(event, LambdaContext())


def test_sqs_fail_inbound_validation():
    event = {"greeting": "hello"}
    with pytest.raises(ValidationError):
        sqs_string_body_handler(event, LambdaContext())
