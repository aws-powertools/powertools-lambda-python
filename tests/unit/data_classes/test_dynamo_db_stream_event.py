from decimal import Clamped, Context, Inexact, Overflow, Rounded, Underflow

from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecordEventName,
    DynamoDBStreamEvent,
    StreamRecord,
    StreamViewType,
)
from tests.functional.utils import load_event


def test_dynamodb_stream_trigger_event():
    decimal_context = Context(
        Emin=-128,
        Emax=126,
        prec=38,
        traps=[Clamped, Overflow, Inexact, Rounded, Underflow],
    )

    raw_event = load_event("dynamoStreamEvent.json")
    parsed_event = DynamoDBStreamEvent(raw_event)

    records = list(parsed_event.records)

    record = records[0]
    record_raw = raw_event["Records"][0]
    assert record.aws_region == record_raw["awsRegion"]
    assert record.event_id == record_raw["eventID"]
    assert record.event_name is DynamoDBRecordEventName.INSERT
    assert record.event_source == record_raw["eventSource"]
    assert record.event_source_arn == record_raw["eventSourceARN"]
    assert record.event_version == record_raw["eventVersion"]
    assert record.user_identity is None
    dynamodb = record.dynamodb
    assert dynamodb is not None
    assert dynamodb.approximate_creation_date_time is None
    keys = dynamodb.keys
    assert keys is not None
    assert keys["Id"] == decimal_context.create_decimal(101)
    assert dynamodb.new_image.get("Message") == record_raw["dynamodb"]["NewImage"]["Message"]["S"]
    assert dynamodb.old_image is None
    assert dynamodb.sequence_number == record_raw["dynamodb"]["SequenceNumber"]
    assert dynamodb.size_bytes == record_raw["dynamodb"]["SizeBytes"]
    assert dynamodb.stream_view_type == StreamViewType.NEW_AND_OLD_IMAGES


def test_dynamodb_stream_record_deserialization():
    byte_list = [s.encode("utf-8") for s in ["item1", "item2"]]
    decimal_context = Context(
        Emin=-128,
        Emax=126,
        prec=38,
        traps=[Clamped, Overflow, Inexact, Rounded, Underflow],
    )
    data = {
        "Keys": {"key1": {"attr1": "value1"}},
        "NewImage": {
            "Name": {"S": "Joe"},
            "Age": {"N": "35"},
            "TypesMap": {
                "M": {
                    "string": {"S": "value"},
                    "number": {"N": "100"},
                    "bool": {"BOOL": True},
                    "dict": {"M": {"key": {"S": "value"}}},
                    "stringSet": {"SS": ["item1", "item2"]},
                    "numberSet": {"NS": ["100", "200", "300"]},
                    "binary": {"B": b"\x00"},
                    "byteSet": {"BS": byte_list},
                    "list": {"L": [{"S": "item1"}, {"N": "3.14159"}, {"BOOL": False}]},
                    "null": {"NULL": True},
                },
            },
        },
    }
    record = StreamRecord(data)
    assert record.new_image == {
        "Name": "Joe",
        "Age": decimal_context.create_decimal("35"),
        "TypesMap": {
            "string": "value",
            "number": decimal_context.create_decimal("100"),
            "bool": True,
            "dict": {"key": "value"},
            "stringSet": {"item1", "item2"},
            "numberSet": {decimal_context.create_decimal(n) for n in ["100", "200", "300"]},
            "binary": b"\x00",
            "byteSet": set(byte_list),
            "list": ["item1", decimal_context.create_decimal("3.14159"), False],
            "null": None,
        },
    }


def test_dynamodb_stream_record_keys_with_no_keys():
    record = StreamRecord({})
    assert record.keys is None


def test_dynamodb_stream_record_keys_overrides_dict_wrapper_keys():
    data = {"Keys": {"key1": {"N": "101"}}}
    record = StreamRecord(data)
    assert record.keys != data.keys()
