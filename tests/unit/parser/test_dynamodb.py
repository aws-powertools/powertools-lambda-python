import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, parse
from tests.functional.utils import load_event
from tests.unit.parser.schemas import MyAdvancedDynamoBusiness, MyDynamoBusiness


def test_dynamo_db_stream_trigger_event():
    raw_event = load_event("dynamoStreamEvent.json")
    parserd_event: MyDynamoBusiness = parse(
        event=raw_event,
        model=MyDynamoBusiness,
        envelope=envelopes.DynamoDBStreamEnvelope,
    )

    assert len(parserd_event) == 2

    # record index 0
    old_image = parserd_event[0]["OldImage"]
    assert old_image is None

    new_image = parserd_event[0]["NewImage"]
    new_image_raw = raw_event["Records"][0]["dynamodb"]["NewImage"]
    assert new_image.Message["S"] == new_image_raw["Message"]["S"]
    assert new_image.Id["N"] == float(new_image_raw["Id"]["N"])

    # record index 1
    old_image = parserd_event[1]["OldImage"]
    old_image_raw = raw_event["Records"][1]["dynamodb"]["OldImage"]
    assert old_image.Message["S"] == old_image_raw["Message"]["S"]
    assert old_image.Id["N"] == float(old_image_raw["Id"]["N"])

    new_image = parserd_event[1]["NewImage"]
    new_image_raw = raw_event["Records"][1]["dynamodb"]["NewImage"]
    assert new_image.Message["S"] == new_image_raw["Message"]["S"]
    assert new_image.Id["N"] == float(new_image_raw["Id"]["N"])


def test_dynamo_db_stream_trigger_event_no_envelope():
    raw_event = load_event("dynamoStreamEvent.json")
    parserd_event: MyAdvancedDynamoBusiness = MyAdvancedDynamoBusiness(**raw_event)

    records = parserd_event.Records
    record = records[0]
    raw_record = raw_event["Records"][0]

    assert record.awsRegion == raw_record["awsRegion"]
    assert record.eventID == raw_record["eventID"]
    assert record.eventName == raw_record["eventName"]
    assert record.eventSource == raw_record["eventSource"]
    assert record.eventSourceARN == raw_record["eventSourceARN"]
    assert record.eventVersion == float(raw_record["eventVersion"])
    assert record.userIdentity is None

    dynamodb = record.dynamodb
    raw_dynamodb = raw_record["dynamodb"]
    assert dynamodb is not None
    assert dynamodb.ApproximateCreationDateTime is None
    assert dynamodb.OldImage is None
    assert dynamodb.SequenceNumber == raw_dynamodb["SequenceNumber"]
    assert dynamodb.SizeBytes == raw_dynamodb["SizeBytes"]
    assert dynamodb.StreamViewType == raw_dynamodb["StreamViewType"]

    keys = dynamodb.Keys
    raw_keys = raw_dynamodb["Keys"]
    assert keys is not None
    id_key = keys["Id"]
    assert id_key["N"] == raw_keys["Id"]["N"]

    message_key = dynamodb.NewImage.Message
    assert message_key is not None
    assert message_key["S"] == "New item!"


def test_validate_event_does_not_conform_with_model_no_envelope():
    raw_event: dict = {"hello": "s"}
    with pytest.raises(ValidationError):
        MyAdvancedDynamoBusiness(**raw_event)


def test_validate_event_does_not_conform_with_model():
    raw_event: dict = {"hello": "s"}
    with pytest.raises(ValidationError):
        parse(event=raw_event, model=MyDynamoBusiness, envelope=envelopes.DynamoDBStreamEnvelope)
