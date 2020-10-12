from typing import Any, Dict, List

import pytest

from aws_lambda_powertools.utilities.parser import envelopes, exceptions, parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyAdvancedDynamoBusiness, MyDynamoBusiness
from tests.functional.parser.utils import load_event


@parser(schema=MyDynamoBusiness, envelope=envelopes.DynamoDBEnvelope)
def handle_dynamodb(event: List[Dict[str, MyDynamoBusiness]], _: LambdaContext):
    assert len(event) == 2
    assert event[0]["OldImage"] is None
    assert event[0]["NewImage"].Message["S"] == "New item!"
    assert event[0]["NewImage"].Id["N"] == 101
    assert event[1]["OldImage"].Message["S"] == "New item!"
    assert event[1]["OldImage"].Id["N"] == 101
    assert event[1]["NewImage"].Message["S"] == "This item has changed"
    assert event[1]["NewImage"].Id["N"] == 101


@parser(schema=MyAdvancedDynamoBusiness)
def handle_dynamodb_no_envelope(event: MyAdvancedDynamoBusiness, _: LambdaContext):
    records = event.Records
    record = records[0]
    assert record.awsRegion == "us-west-2"
    dynamodb = record.dynamodb
    assert dynamodb is not None
    assert dynamodb.ApproximateCreationDateTime is None
    keys = dynamodb.Keys
    assert keys is not None
    id_key = keys["Id"]
    assert id_key["N"] == "101"
    message_key = dynamodb.NewImage.Message
    assert message_key is not None
    assert message_key["S"] == "New item!"
    assert dynamodb.OldImage is None
    assert dynamodb.SequenceNumber == "111"
    assert dynamodb.SizeBytes == 26
    assert dynamodb.StreamViewType == "NEW_AND_OLD_IMAGES"
    assert record.eventID == "1"
    assert record.eventName == "INSERT"
    assert record.eventSource == "aws:dynamodb"
    assert record.eventSourceARN == "eventsource_arn"
    assert record.eventVersion == 1.0
    assert record.userIdentity is None


def test_dynamo_db_stream_trigger_event():
    event_dict = load_event("dynamoStreamEvent.json")
    handle_dynamodb(event_dict, LambdaContext())


def test_dynamo_db_stream_trigger_event_no_envelope():
    event_dict = load_event("dynamoStreamEvent.json")
    handle_dynamodb_no_envelope(event_dict, LambdaContext())


def test_validate_event_does_not_conform_with_schema_no_envelope():
    event_dict: Any = {"hello": "s"}
    with pytest.raises(exceptions.SchemaValidationError):
        handle_dynamodb_no_envelope(event_dict, LambdaContext())


def test_validate_event_does_not_conform_with_schema():
    event_dict: Any = {"hello": "s"}
    with pytest.raises(exceptions.SchemaValidationError):
        handle_dynamodb(event_dict, LambdaContext())
