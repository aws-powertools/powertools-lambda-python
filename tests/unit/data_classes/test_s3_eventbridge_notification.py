from typing import Dict

import pytest

from aws_lambda_powertools.utilities.data_classes.s3_event import (
    S3EventBridgeNotificationEvent,
)
from tests.functional.utils import load_event


@pytest.mark.parametrize(
    "raw_event",
    [
        pytest.param(load_event("s3EventBridgeNotificationObjectCreatedEvent.json")),
        pytest.param(load_event("s3EventBridgeNotificationObjectDeletedEvent.json")),
        pytest.param(load_event("s3EventBridgeNotificationObjectExpiredEvent.json")),
        pytest.param(load_event("s3EventBridgeNotificationObjectRestoreCompletedEvent.json")),
    ],
    ids=["object_created", "object_deleted", "object_expired", "object_restored"],
)
def test_s3_eventbridge_notification_detail_parsed(raw_event: Dict):
    parsed_event = S3EventBridgeNotificationEvent(raw_event)

    assert parsed_event.version == raw_event["version"]
    assert parsed_event.detail.bucket.name == raw_event["detail"]["bucket"]["name"]
    assert parsed_event.detail.deletion_type == raw_event["detail"].get("deletion-type")
    assert parsed_event.detail.destination_access_tier == raw_event["detail"].get("destination-access-tier")
    assert parsed_event.detail.destination_storage_class == raw_event["detail"].get("destination-storage-class")
    assert parsed_event.detail.object.etag == raw_event["detail"]["object"]["etag"]
    assert parsed_event.detail.object.key == raw_event["detail"]["object"]["key"]
    assert parsed_event.detail.object.sequencer == raw_event["detail"]["object"]["sequencer"]
    assert parsed_event.detail.object.size == raw_event["detail"]["object"]["size"]
    assert parsed_event.detail.reason == raw_event["detail"].get("reason")
    assert parsed_event.detail.version == raw_event["detail"].get("version")
    assert parsed_event.detail.request_id == raw_event["detail"]["request-id"]
    assert parsed_event.detail.requester == raw_event["detail"]["requester"]
    assert parsed_event.detail.restore_expiry_time == raw_event["detail"].get("restore-expiry-time")
    assert parsed_event.detail.source_ip_address == raw_event["detail"].get("source-ip-address")
    assert parsed_event.detail.source_storage_class == raw_event["detail"].get("source-storage-class")
