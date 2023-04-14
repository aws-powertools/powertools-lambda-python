from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.parser.models import (
    SqsS3EventNotificationModel,
    S3Model,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.schemas import MyAdvancedSqsBusiness
from tests.functional.utils import json_serialize, load_event

@event_parser(model=SqsS3EventNotificationModel)
def handle_sqs_json_body_containing_s3_notifications(event: SqsS3EventNotificationModel, _: LambdaContext):
    return event

@event_parser(model=MyAdvancedSqsBusiness)
def generate_sqs_event() -> MyAdvancedSqsBusiness:
    return load_event("sqsEvent.json")

@event_parser(model=S3Model)
def generate_s3_event_notification() -> S3Model:
    return load_event("s3Event.json")

def test_handle_sqs_json_body_containing_s3_notifications():
    sqs_event = generate_sqs_event()
    s3_event_notification = generate_s3_event_notification()
    for record in sqs_event.Records:
        record.body = json_serialize(s3_event_notification)

    parsed_event: SqsS3EventNotificationModel = handle_sqs_json_body_containing_s3_notifications(sqs_event, LambdaContext())

    assert len(parsed_event.Records) == 2
    for parsed_sqs_record in parsed_event.Records:
        assert_s3(parsed_sqs_record.body)
