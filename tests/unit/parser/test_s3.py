import json
from datetime import datetime

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError
from aws_lambda_powertools.utilities.parser.models import (
    S3EventNotificationEventBridgeModel,
    S3SqsEventNotificationModel,
)
from tests.functional.utils import load_event


def test_s3_eventbridge_notification_object_created_event():
    raw_event = load_event("s3EventBridgeNotificationObjectCreatedEvent.json")
    model = S3EventNotificationEventBridgeModel(**raw_event)

    assert model.version == raw_event["version"]
    assert model.id == raw_event["id"]
    assert model.detail_type == raw_event["detail-type"]
    assert model.source == raw_event["source"]
    assert model.account == raw_event["account"]
    assert model.time == datetime.fromisoformat(raw_event["time"].replace("Z", "+00:00"))
    assert model.region == raw_event["region"]
    assert model.resources == raw_event["resources"]

    assert model.detail.version == raw_event["detail"]["version"]
    assert model.detail.bucket.name == raw_event["detail"]["bucket"]["name"]
    assert model.detail.object.key == raw_event["detail"]["object"]["key"]
    assert model.detail.object.size == raw_event["detail"]["object"]["size"]
    assert model.detail.object.etag == raw_event["detail"]["object"]["etag"]
    assert model.detail.object.sequencer == raw_event["detail"]["object"]["sequencer"]
    assert model.detail.request_id == raw_event["detail"]["request-id"]
    assert model.detail.requester == raw_event["detail"]["requester"]
    assert model.detail.source_ip_address == raw_event["detail"]["source-ip-address"]
    assert model.detail.reason == raw_event["detail"]["reason"]


def test_s3_eventbridge_notification_object_deleted_event():
    raw_event = load_event("s3EventBridgeNotificationObjectDeletedEvent.json")
    model = S3EventNotificationEventBridgeModel(**raw_event)

    assert model.version == raw_event["version"]
    assert model.id == raw_event["id"]
    assert model.detail_type == raw_event["detail-type"]
    assert model.source == raw_event["source"]
    assert model.account == raw_event["account"]
    assert model.time == datetime.fromisoformat(raw_event["time"].replace("Z", "+00:00"))
    assert model.region == raw_event["region"]
    assert model.resources == raw_event["resources"]

    assert model.detail.version == raw_event["detail"]["version"]
    assert model.detail.bucket.name == raw_event["detail"]["bucket"]["name"]
    assert model.detail.object.key == raw_event["detail"]["object"]["key"]
    assert model.detail.object.size == raw_event["detail"]["object"]["size"]
    assert model.detail.object.etag == raw_event["detail"]["object"]["etag"]
    assert model.detail.object.sequencer == raw_event["detail"]["object"]["sequencer"]
    assert model.detail.request_id == raw_event["detail"]["request-id"]
    assert model.detail.requester == raw_event["detail"]["requester"]
    assert model.detail.source_ip_address == raw_event["detail"]["source-ip-address"]
    assert model.detail.reason == raw_event["detail"]["reason"]
    assert model.detail.deletion_type == raw_event["detail"]["deletion-type"]


def test_s3_eventbridge_notification_object_expired_event():
    raw_event = load_event("s3EventBridgeNotificationObjectExpiredEvent.json")
    model = S3EventNotificationEventBridgeModel(**raw_event)

    assert model.version == raw_event["version"]
    assert model.id == raw_event["id"]
    assert model.detail_type == raw_event["detail-type"]
    assert model.source == raw_event["source"]
    assert model.account == raw_event["account"]
    assert model.time == datetime.fromisoformat(raw_event["time"].replace("Z", "+00:00"))
    assert model.region == raw_event["region"]
    assert model.resources == raw_event["resources"]

    assert model.detail.version == raw_event["detail"]["version"]
    assert model.detail.bucket.name == raw_event["detail"]["bucket"]["name"]
    assert model.detail.object.key == raw_event["detail"]["object"]["key"]
    assert model.detail.object.size == raw_event["detail"]["object"]["size"]
    assert model.detail.object.etag == raw_event["detail"]["object"]["etag"]
    assert model.detail.object.sequencer == raw_event["detail"]["object"]["sequencer"]
    assert model.detail.request_id == raw_event["detail"]["request-id"]
    assert model.detail.requester == raw_event["detail"]["requester"]
    assert model.detail.reason == raw_event["detail"]["reason"]
    assert model.detail.deletion_type == raw_event["detail"]["deletion-type"]


def test_s3_eventbridge_notification_object_restore_completed_event():
    raw_event = load_event("s3EventBridgeNotificationObjectRestoreCompletedEvent.json")
    model = S3EventNotificationEventBridgeModel(**raw_event)

    assert model.version == raw_event["version"]
    assert model.id == raw_event["id"]
    assert model.detail_type == raw_event["detail-type"]
    assert model.source == raw_event["source"]
    assert model.account == raw_event["account"]
    assert model.time == datetime.fromisoformat(raw_event["time"].replace("Z", "+00:00"))
    assert model.region == raw_event["region"]
    assert model.resources == raw_event["resources"]

    assert model.detail.version == raw_event["detail"]["version"]
    assert model.detail.bucket.name == raw_event["detail"]["bucket"]["name"]
    assert model.detail.object.key == raw_event["detail"]["object"]["key"]
    assert model.detail.object.size == raw_event["detail"]["object"]["size"]
    assert model.detail.object.etag == raw_event["detail"]["object"]["etag"]
    assert model.detail.object.sequencer == raw_event["detail"]["object"]["sequencer"]
    assert model.detail.request_id == raw_event["detail"]["request-id"]
    assert model.detail.requester == raw_event["detail"]["requester"]
    assert model.detail.restore_expiry_time == raw_event["detail"]["restore-expiry-time"]
    assert model.detail.source_storage_class == raw_event["detail"]["source-storage-class"]


def test_s3_sqs_event_notification():
    raw_event = load_event("sqsS3Event.json")
    model = S3SqsEventNotificationModel(**raw_event)

    body = json.loads(raw_event["Records"][0]["body"])

    assert model.Records[0].body.Records[0].eventVersion == body["Records"][0]["eventVersion"]
    assert model.Records[0].body.Records[0].eventSource == body["Records"][0]["eventSource"]
    assert model.Records[0].body.Records[0].eventTime == datetime.fromisoformat(
        body["Records"][0]["eventTime"].replace("Z", "+00:00")
    )
    assert model.Records[0].body.Records[0].eventName == body["Records"][0]["eventName"]


def test_s3_sqs_event_notification_body_invalid_json():
    raw_event = load_event("s3Event.json")

    with pytest.raises(ValidationError):
        S3SqsEventNotificationModel(**raw_event)


def test_s3_sqs_event_notification_body_containing_arbitrary_json():
    raw_event = load_event("sqsS3Event.json")
    for record in raw_event["Records"]:
        record["body"] = {"foo": "bar"}

    with pytest.raises(ValidationError):
        S3SqsEventNotificationModel(**raw_event)
