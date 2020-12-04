import base64
import json
import zlib
from typing import Any, List

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, envelopes, event_parser
from aws_lambda_powertools.utilities.parser.models import CloudWatchLogsLogEvent, CloudWatchLogsModel
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyCloudWatchBusiness
from tests.functional.parser.utils import load_event


@event_parser(model=MyCloudWatchBusiness, envelope=envelopes.CloudWatchLogsEnvelope)
def handle_cloudwatch_logs(event: List[MyCloudWatchBusiness], _: LambdaContext):
    assert len(event) == 1
    log: MyCloudWatchBusiness = event[0]
    assert log.my_message == "hello"
    assert log.user == "test"


@event_parser(model=CloudWatchLogsModel)
def handle_cloudwatch_logs_no_envelope(event: CloudWatchLogsModel, _: LambdaContext):
    assert event.awslogs.decoded_data.owner == "123456789123"
    assert event.awslogs.decoded_data.logGroup == "testLogGroup"
    assert event.awslogs.decoded_data.logStream == "testLogStream"
    assert event.awslogs.decoded_data.subscriptionFilters == ["testFilter"]
    assert event.awslogs.decoded_data.messageType == "DATA_MESSAGE"

    assert len(event.awslogs.decoded_data.logEvents) == 2
    log_record: CloudWatchLogsLogEvent = event.awslogs.decoded_data.logEvents[0]
    assert log_record.id == "eventId1"
    convert_time = int(round(log_record.timestamp.timestamp() * 1000))
    assert convert_time == 1440442987000
    assert log_record.message == "[ERROR] First test message"
    log_record: CloudWatchLogsLogEvent = event.awslogs.decoded_data.logEvents[1]
    assert log_record.id == "eventId2"
    convert_time = int(round(log_record.timestamp.timestamp() * 1000))
    assert convert_time == 1440442987001
    assert log_record.message == "[ERROR] Second test message"


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
    event_dict = load_event("cloudWatchLogEvent.json")
    handle_cloudwatch_logs_no_envelope(event_dict, LambdaContext())


def test_handle_invalid_cloudwatch_trigger_event_no_envelope():
    event_dict: Any = {"awslogs": {"data": "invalid_data"}}
    with pytest.raises(ValidationError) as context:
        handle_cloudwatch_logs_no_envelope(event_dict, LambdaContext())

    assert context.value.errors()[0]["msg"] == "unable to decompress data"


def test_handle_invalid_event_with_envelope():
    with pytest.raises(ValidationError):
        handle_cloudwatch_logs(event={}, context=LambdaContext())
