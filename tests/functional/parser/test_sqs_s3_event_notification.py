import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, event_parser
from aws_lambda_powertools.utilities.parser.models import SqsS3EventNotificationModel
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.test_s3 import assert_s3
from tests.functional.utils import json_serialize, load_event


@event_parser(model=SqsS3EventNotificationModel)
def handle_sqs_json_body_containing_s3_notifications(event: SqsS3EventNotificationModel, _: LambdaContext):
    return event


def test_handle_sqs_json_body_containing_s3_notifications():
    sqs_event_dict = load_event("sqsEvent.json")
    s3_event_notification_dict = load_event("s3Event.json")
    for record in sqs_event_dict["Records"]:
        record["body"] = json_serialize(s3_event_notification_dict)

    parsed_event: SqsS3EventNotificationModel = handle_sqs_json_body_containing_s3_notifications(
        sqs_event_dict, LambdaContext()
    )

    assert len(parsed_event.Records) == 2
    for parsed_sqs_record in parsed_event.Records:
        assert_s3(parsed_sqs_record.body)


def test_handle_sqs_body_invalid_json():
    sqs_event_dict = load_event("sqsEvent.json")

    with pytest.raises(ValidationError):
        handle_sqs_json_body_containing_s3_notifications(sqs_event_dict, LambdaContext())


def test_handle_sqs_json_body_containing_arbitrary_json():
    sqs_event_dict = load_event("sqsEvent.json")
    for record in sqs_event_dict["Records"]:
        record["body"] = json_serialize({"foo": "bar"})

    with pytest.raises(ValidationError):
        handle_sqs_json_body_containing_s3_notifications(sqs_event_dict, LambdaContext())
