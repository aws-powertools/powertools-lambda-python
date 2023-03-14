from datetime import datetime

from aws_lambda_powertools.utilities.parser.models import (
    S3EventNotificationEventBridgeModel,
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
