from aws_lambda_powertools.utilities.data_classes.s3_event import (
    S3EventBridgeNotificationDetail,
    S3EventBridgeNotificationEvent,
    S3EventBridgeNotificationObject,
)
from tests.functional.utils import load_event


def test_s3_eventbridge_notification_detail_parsed_object_created():
    event = S3EventBridgeNotificationEvent(load_event("s3EventBridgeNotificationObjectCreatedEvent.json"))
    bucket_name = "example-bucket"
    deletion_type = None
    destination_access_tier = None
    destination_storage_class = None
    detail: S3EventBridgeNotificationDetail = event.detail
    _object: S3EventBridgeNotificationObject = detail.object
    reason = "PutObject"
    request_id = "57H08PA84AB1JZW0"
    requester = "123456789012"
    restore_expiry_time = None
    source_ip_address = "34.252.34.74"
    source_storage_class = None
    version = "0"

    assert bucket_name == event.detail.bucket.name
    assert deletion_type == event.detail.deletion_type
    assert destination_access_tier == event.detail.destination_access_tier
    assert destination_storage_class == event.detail.destination_storage_class
    assert _object == event.detail.object
    assert reason == event.detail.reason
    assert request_id == event.detail.request_id
    assert requester == event.detail.requester
    assert restore_expiry_time == event.detail.restore_expiry_time
    assert source_ip_address == event.detail.source_ip_address
    assert source_storage_class == event.detail.source_storage_class
    assert version == event.version


def test_s3_eventbridge_notification_detail_parsed_object_deleted():
    event = S3EventBridgeNotificationEvent(load_event("s3EventBridgeNotificationObjectDeletedEvent.json"))
    bucket_name = "example-bucket"
    deletion_type = "Delete Marker Created"
    destination_access_tier = None
    destination_storage_class = None
    detail: S3EventBridgeNotificationDetail = event.detail
    _object: S3EventBridgeNotificationObject = detail.object
    reason = "DeleteObject"
    request_id = "0BH729840619AG5K"
    requester = "123456789012"
    restore_expiry_time = None
    source_ip_address = "34.252.34.74"
    source_storage_class = None
    version = "0"

    assert bucket_name == event.detail.bucket.name
    assert deletion_type == event.detail.deletion_type
    assert destination_access_tier == event.detail.destination_access_tier
    assert destination_storage_class == event.detail.destination_storage_class
    assert _object == event.detail.object
    assert reason == event.detail.reason
    assert request_id == event.detail.request_id
    assert requester == event.detail.requester
    assert restore_expiry_time == event.detail.restore_expiry_time
    assert source_ip_address == event.detail.source_ip_address
    assert source_storage_class == event.detail.source_storage_class
    assert version == event.version


def test_s3_eventbridge_notification_detail_parsed_object_expired():
    event = S3EventBridgeNotificationEvent(load_event("s3EventBridgeNotificationObjectExpiredEvent.json"))
    bucket_name = "example-bucket"
    deletion_type = "Delete Marker Created"
    destination_access_tier = None
    destination_storage_class = None
    detail: S3EventBridgeNotificationDetail = event.detail
    _object: S3EventBridgeNotificationObject = detail.object
    reason = "Lifecycle Expiration"
    request_id = "20EB74C14654DC47"
    requester = "s3.amazonaws.com"
    restore_expiry_time = None
    source_ip_address = None
    source_storage_class = None
    version = "0"

    assert bucket_name == event.detail.bucket.name
    assert deletion_type == event.detail.deletion_type
    assert destination_access_tier == event.detail.destination_access_tier
    assert destination_storage_class == event.detail.destination_storage_class
    assert _object == event.detail.object
    assert reason == event.detail.reason
    assert request_id == event.detail.request_id
    assert requester == event.detail.requester
    assert restore_expiry_time == event.detail.restore_expiry_time
    assert source_ip_address == event.detail.source_ip_address
    assert source_storage_class == event.detail.source_storage_class
    assert version == event.version


def test_s3_eventbridge_notification_detail_parsed_object_restore_completed():
    event = S3EventBridgeNotificationEvent(load_event("s3EventBridgeNotificationObjectRestoreCompletedEvent.json"))
    bucket_name = "example-bucket"
    deletion_type = None
    destination_access_tier = None
    destination_storage_class = None
    detail: S3EventBridgeNotificationDetail = event.detail
    _object: S3EventBridgeNotificationObject = detail.object
    reason = None
    request_id = "189F19CB7FB1B6A4"
    requester = "s3.amazonaws.com"
    restore_expiry_time = "2021-11-13T00:00:00Z"
    source_ip_address = None
    source_storage_class = "GLACIER"
    version = "0"

    assert bucket_name == event.detail.bucket.name
    assert deletion_type == event.detail.deletion_type
    assert destination_access_tier == event.detail.destination_access_tier
    assert destination_storage_class == event.detail.destination_storage_class
    assert _object == event.detail.object
    assert reason == event.detail.reason
    assert request_id == event.detail.request_id
    assert requester == event.detail.requester
    assert restore_expiry_time == event.detail.restore_expiry_time
    assert source_ip_address == event.detail.source_ip_address
    assert source_storage_class == event.detail.source_storage_class
    assert version == event.version
