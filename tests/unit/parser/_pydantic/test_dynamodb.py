from typing import Any

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, parse
from aws_lambda_powertools.utilities.parser.models import DynamoDBStreamLambdaOnFailureDestinationModel
from tests.functional.utils import load_event
from tests.unit.parser._pydantic.schemas import MyAdvancedDynamoBusiness, MyDynamoBusiness


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
    assert new_image.Message == new_image_raw["Message"]["S"]
    assert new_image.Id == float(new_image_raw["Id"]["N"])

    # record index 1
    old_image = parserd_event[1]["OldImage"]
    old_image_raw = raw_event["Records"][1]["dynamodb"]["OldImage"]
    assert old_image.Message == old_image_raw["Message"]["S"]
    assert old_image.Id == float(old_image_raw["Id"]["N"])

    new_image = parserd_event[1]["NewImage"]
    new_image_raw = raw_event["Records"][1]["dynamodb"]["NewImage"]
    assert new_image.Message == new_image_raw["Message"]["S"]
    assert new_image.Id == float(new_image_raw["Id"]["N"])


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
    assert dynamodb.ApproximateCreationDateTime is not None
    assert dynamodb.ApproximateCreationDateTime.timestamp() == raw_dynamodb["ApproximateCreationDateTime"]
    assert dynamodb.OldImage is None
    assert dynamodb.SequenceNumber == raw_dynamodb["SequenceNumber"]
    assert dynamodb.SizeBytes == raw_dynamodb["SizeBytes"]
    assert dynamodb.StreamViewType == raw_dynamodb["StreamViewType"]

    keys = dynamodb.Keys
    raw_keys = raw_dynamodb["Keys"]
    assert keys is not None
    id_key = keys.get("Id")
    assert id_key == int(raw_keys["Id"]["N"])

    message_key = dynamodb.NewImage.Message
    assert message_key is not None
    assert message_key == "New item!"


def test_validate_event_does_not_conform_with_model_no_envelope():
    raw_event: dict = {"hello": "s"}
    with pytest.raises(ValidationError):
        MyAdvancedDynamoBusiness(**raw_event)


def test_validate_event_does_not_conform_with_model():
    raw_event: dict = {"hello": "s"}
    with pytest.raises(ValidationError):
        parse(event=raw_event, model=MyDynamoBusiness, envelope=envelopes.DynamoDBStreamEnvelope)


@pytest.mark.parametrize(
    "response_context",
    [
        pytest.param(
            {"statusCode": 200, "executedVersion": "$LATEST"},
            id="without function error",
        ),
        pytest.param(
            {"statusCode": 200, "executedVersion": "$LATEST", "functionError": None},
            id="with null function error",
        ),
        pytest.param(
            {"statusCode": 200, "executedVersion": "$LATEST", "functionError": "Unhandled"},
            id="with function error",
        ),
    ],
)
def test_dynamo_db_stream_lambda_invocation_event(response_context: dict[str, Any]):
    raw_event = load_event("dynamoStreamLambdaInvocationEvent.json")
    raw_event["responseContext"] = response_context
    parsed_event: DynamoDBStreamLambdaOnFailureDestinationModel = parse(
        event=raw_event,
        model=DynamoDBStreamLambdaOnFailureDestinationModel,
    )
    assert (
        parsed_event.ddb_stream_batch_info.approximate_arrival_of_first_record.strftime("%Y-%m-%dT%H:%M:%SZ")
        == raw_event["DDBStreamBatchInfo"]["approximateArrivalOfFirstRecord"]
    )
    assert (
        parsed_event.ddb_stream_batch_info.approximate_arrival_of_last_record.strftime("%Y-%m-%dT%H:%M:%SZ")
        == raw_event["DDBStreamBatchInfo"]["approximateArrivalOfLastRecord"]
    )
    assert parsed_event.ddb_stream_batch_info.batch_size == raw_event["DDBStreamBatchInfo"]["batchSize"]
    assert (
        parsed_event.ddb_stream_batch_info.end_sequence_number == raw_event["DDBStreamBatchInfo"]["endSequenceNumber"]
    )
    assert parsed_event.ddb_stream_batch_info.shard_id == raw_event["DDBStreamBatchInfo"]["shardId"]
    assert (
        parsed_event.ddb_stream_batch_info.start_sequence_number
        == raw_event["DDBStreamBatchInfo"]["startSequenceNumber"]
    )
    assert parsed_event.ddb_stream_batch_info.stream_arn == raw_event["DDBStreamBatchInfo"]["streamArn"]
    assert parsed_event.request_context.model_dump(by_alias=True) == raw_event["requestContext"]
    assert parsed_event.response_context.status_code == response_context["statusCode"]
    assert parsed_event.response_context.executed_version == response_context["executedVersion"]
    assert parsed_event.response_context.function_error == response_context.get("functionError")
    assert parsed_event.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == raw_event["timestamp"]
    assert parsed_event.version == raw_event["version"]
