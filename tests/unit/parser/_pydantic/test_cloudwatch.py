import base64
import json
import zlib
from typing import Any

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, parse
from aws_lambda_powertools.utilities.parser.models import (
    CloudWatchLogsLogEvent,
    CloudWatchLogsModel,
)
from tests.functional.utils import load_event
from tests.unit.parser._pydantic.schemas import MyCloudWatchBusiness


def decode_cloudwatch_raw_event(event: dict):
    payload = base64.b64decode(event)
    uncompressed = zlib.decompress(payload, zlib.MAX_WBITS | 32)
    return json.loads(uncompressed.decode("utf-8"))


def test_validate_event_user_model_with_envelope():
    my_log_message = {"my_message": "hello", "user": "test"}
    inner_event_dict = {
        "messageType": "DATA_MESSAGE",
        "owner": "123456789123",
        "logGroup": "testLogGroup",
        "logStream": "testLogStream",
        "subscriptionFilters": ["testFilter"],
        "logEvents": [{"id": "eventId1", "timestamp": 1440442987000, "message": json.dumps(my_log_message)}],
    }
    dict_str = json.dumps(inner_event_dict)
    compressesd_str = zlib.compress(str.encode(dict_str), -1)
    raw_event = {"awslogs": {"data": base64.b64encode(compressesd_str)}}

    parsed_event: MyCloudWatchBusiness = parse(
        event=raw_event,
        model=MyCloudWatchBusiness,
        envelope=envelopes.CloudWatchLogsEnvelope,
    )

    assert len(parsed_event) == 1
    log: MyCloudWatchBusiness = parsed_event[0]
    assert log.my_message == "hello"
    assert log.user == "test"


def test_validate_event_does_not_conform_with_user_dict_model():
    event_dict = load_event("cloudWatchLogEvent.json")
    with pytest.raises(ValidationError):
        MyCloudWatchBusiness(**event_dict)


def test_handle_cloudwatch_trigger_event_no_envelope():
    raw_event = load_event("cloudWatchLogEvent.json")
    parsed_event: CloudWatchLogsModel = CloudWatchLogsModel(**raw_event)

    raw_event_decoded = decode_cloudwatch_raw_event(raw_event["awslogs"]["data"])

    assert parsed_event.awslogs.decoded_data.owner == raw_event_decoded["owner"]
    assert parsed_event.awslogs.decoded_data.logGroup == raw_event_decoded["logGroup"]
    assert parsed_event.awslogs.decoded_data.logStream == raw_event_decoded["logStream"]
    assert parsed_event.awslogs.decoded_data.subscriptionFilters == raw_event_decoded["subscriptionFilters"]
    assert parsed_event.awslogs.decoded_data.messageType == raw_event_decoded["messageType"]
    assert parsed_event.awslogs.decoded_data.policyLevel is None

    assert len(parsed_event.awslogs.decoded_data.logEvents) == 2

    log_record: CloudWatchLogsLogEvent = parsed_event.awslogs.decoded_data.logEvents[0]
    raw_log_record = raw_event_decoded["logEvents"][0]
    assert log_record.id == raw_log_record["id"]
    convert_time = int(round(log_record.timestamp.timestamp() * 1000))
    assert convert_time == raw_log_record["timestamp"]
    assert log_record.message == raw_log_record["message"]

    log_record: CloudWatchLogsLogEvent = parsed_event.awslogs.decoded_data.logEvents[1]
    raw_log_record = raw_event_decoded["logEvents"][1]
    assert log_record.id == raw_log_record["id"]
    convert_time = int(round(log_record.timestamp.timestamp() * 1000))
    assert convert_time == raw_log_record["timestamp"]
    assert log_record.message == raw_log_record["message"]


def test_handle_cloudwatch_trigger_event_no_envelope_with_policylevel():
    raw_event = load_event("cloudWatchLogEventWithPolicyLevel.json")
    parsed_event: CloudWatchLogsModel = CloudWatchLogsModel(**raw_event)

    raw_event_decoded = decode_cloudwatch_raw_event(raw_event["awslogs"]["data"])

    assert parsed_event.awslogs.decoded_data.owner == raw_event_decoded["owner"]
    assert parsed_event.awslogs.decoded_data.logGroup == raw_event_decoded["logGroup"]
    assert parsed_event.awslogs.decoded_data.logStream == raw_event_decoded["logStream"]
    assert parsed_event.awslogs.decoded_data.subscriptionFilters == raw_event_decoded["subscriptionFilters"]
    assert parsed_event.awslogs.decoded_data.messageType == raw_event_decoded["messageType"]
    assert parsed_event.awslogs.decoded_data.policyLevel == "ACCOUNT_LEVEL_POLICY"

    assert len(parsed_event.awslogs.decoded_data.logEvents) == 2

    log_record: CloudWatchLogsLogEvent = parsed_event.awslogs.decoded_data.logEvents[0]
    raw_log_record = raw_event_decoded["logEvents"][0]
    assert log_record.id == raw_log_record["id"]
    convert_time = int(round(log_record.timestamp.timestamp() * 1000))
    assert convert_time == raw_log_record["timestamp"]
    assert log_record.message == raw_log_record["message"]

    log_record: CloudWatchLogsLogEvent = parsed_event.awslogs.decoded_data.logEvents[1]
    raw_log_record = raw_event_decoded["logEvents"][1]
    assert log_record.id == raw_log_record["id"]
    convert_time = int(round(log_record.timestamp.timestamp() * 1000))
    assert convert_time == raw_log_record["timestamp"]
    assert log_record.message == raw_log_record["message"]


def test_handle_invalid_cloudwatch_trigger_event_no_envelope():
    raw_event: Any = {"awslogs": {"data": "invalid_data"}}
    with pytest.raises(ValidationError) as context:
        CloudWatchLogsModel(**raw_event)

    # Pydantic v2 adds "Value error," to the error string.
    # So to maintain compatibility with v1 and v2, we've changed the way we test this.
    assert "unable to decompress data" in context.value.errors()[0]["msg"]


def test_handle_invalid_event_with_envelope():
    empty_dict = {}
    with pytest.raises(ValidationError):
        CloudWatchLogsModel(**empty_dict)


def _make_cloudwatch_event(messages: list[str]) -> dict:
    inner_event_dict = {
        "messageType": "DATA_MESSAGE",
        "owner": "123456789012",
        "logGroup": "/aws/lambda/my-function",
        "logStream": "2024/10/21/[$LATEST]abcdef1234567890",
        "subscriptionFilters": ["my-filter"],
        "logEvents": [
            {"id": f"event-{i}", "timestamp": 1729520895158 + i, "message": message}
            for i, message in enumerate(messages)
        ],
    }
    compressed = zlib.compress(json.dumps(inner_event_dict).encode("utf-8"), -1)
    return {"awslogs": {"data": base64.b64encode(compressed)}}


def test_cloudwatch_envelope_handles_non_json_messages():
    plain_text_messages = [
        "START RequestId: eadc91c8-8273-4a2d-b170-b0a7883b619e Version: $LATEST\n",
        "2024-10-21T14:28:15.158Z\teadc91c8-8273-4a2d-b170-b0a7883b619e\tINFO\tHello from handler\n",
        "END RequestId: eadc91c8-8273-4a2d-b170-b0a7883b619e\n",
        (
            "REPORT RequestId: eadc91c8-8273-4a2d-b170-b0a7883b619e\tDuration: 2.07 ms\t"
            "Billed Duration: 3 ms\tMemory Size: 128 MB\tMax Memory Used: 67 MB\t\n"
        ),
    ]

    parsed = parse(
        event=_make_cloudwatch_event(plain_text_messages),
        model=str,
        envelope=envelopes.CloudWatchLogsEnvelope,
    )

    assert parsed == plain_text_messages


def test_cloudwatch_envelope_handles_mixed_json_and_plain_text_messages():
    messages = [
        json.dumps({"my_message": "hello", "user": "test"}),
        "START RequestId: eadc91c8-8273-4a2d-b170-b0a7883b619e Version: $LATEST\n",
    ]

    parsed = parse(
        event=_make_cloudwatch_event(messages),
        model=str,
        envelope=envelopes.CloudWatchLogsEnvelope,
    )

    assert parsed == messages


def test_cloudwatch_envelope_plain_text_still_fails_for_object_model():
    with pytest.raises(ValidationError):
        parse(
            event=_make_cloudwatch_event(["START RequestId: eadc91c8-8273-4a2d-b170-b0a7883b619e\n"]),
            model=MyCloudWatchBusiness,
            envelope=envelopes.CloudWatchLogsEnvelope,
        )
