import base64
import json
import zlib
from typing import Any, List

import pytest

from aws_lambda_powertools.utilities.parser import (
    ValidationError,
    envelopes,
    event_parser,
)
from aws_lambda_powertools.utilities.parser.models import (
    CloudWatchLogsLogEvent,
    CloudWatchLogsModel,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyCloudWatchBusiness
from tests.functional.utils import load_event


def decode_cloudwatch_raw_event(event: dict):
    payload = base64.b64decode(event)
    uncompressed = zlib.decompress(payload, zlib.MAX_WBITS | 32)
    return json.loads(uncompressed.decode("utf-8"))


@event_parser(model=MyCloudWatchBusiness, envelope=envelopes.CloudWatchLogsEnvelope)
def handle_cloudwatch_logs(event: List[MyCloudWatchBusiness], _: LambdaContext):
    assert len(event) == 1
    log: MyCloudWatchBusiness = event[0]
    assert log.my_message == "hello"
    assert log.user == "test"


@event_parser(model=CloudWatchLogsModel)
def handle_cloudwatch_logs_no_envelope(event: CloudWatchLogsModel, _: LambdaContext):
    return event


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
    event_dict = {"awslogs": {"data": base64.b64encode(compressesd_str)}}

    handle_cloudwatch_logs(event_dict, LambdaContext())


def test_validate_event_does_not_conform_with_user_dict_model():
    event_dict = load_event("cloudWatchLogEvent.json")
    with pytest.raises(ValidationError):
        handle_cloudwatch_logs(event_dict, LambdaContext())


def test_handle_cloudwatch_trigger_event_no_envelope():
    raw_event = load_event("cloudWatchLogEvent.json")
    parsed_event: CloudWatchLogsModel = handle_cloudwatch_logs_no_envelope(raw_event, LambdaContext())

    raw_event_decoded = decode_cloudwatch_raw_event(raw_event["awslogs"]["data"])

    assert parsed_event.awslogs.decoded_data.owner == raw_event_decoded["owner"]
    assert parsed_event.awslogs.decoded_data.logGroup == raw_event_decoded["logGroup"]
    assert parsed_event.awslogs.decoded_data.logStream == raw_event_decoded["logStream"]
    assert parsed_event.awslogs.decoded_data.subscriptionFilters == raw_event_decoded["subscriptionFilters"]
    assert parsed_event.awslogs.decoded_data.messageType == raw_event_decoded["messageType"]

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
    event_dict: Any = {"awslogs": {"data": "invalid_data"}}
    with pytest.raises(ValidationError) as context:
        handle_cloudwatch_logs_no_envelope(event_dict, LambdaContext())

    assert context.value.errors()[0]["msg"] == "unable to decompress data"


def test_handle_invalid_event_with_envelope():
    with pytest.raises(ValidationError):
        handle_cloudwatch_logs(event={}, context=LambdaContext())
