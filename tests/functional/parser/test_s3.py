from datetime import datetime

import pytest

from aws_lambda_powertools.utilities.parser import ValidationError, event_parser, parse
from aws_lambda_powertools.utilities.parser.envelopes import EventBridgeEnvelope
from aws_lambda_powertools.utilities.parser.models import (
    S3EventNotificationEventBridgeDetailModel,
    S3EventNotificationEventBridgeModel,
    S3EventNotificationObjectModel,
    S3Model,
    S3RecordModel,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.utils import load_event


@event_parser(model=S3Model)
def handle_s3(event: S3Model, _: LambdaContext):
    records = list(event.Records)
    assert len(records) == 1
    record: S3RecordModel = records[0]
    assert record.eventVersion == "2.1"
    assert record.eventSource == "aws:s3"
    assert record.awsRegion == "us-east-2"
    convert_time = int(round(record.eventTime.timestamp() * 1000))
    assert convert_time == 1567539447192
    assert record.eventName == "ObjectCreated:Put"
    user_identity = record.userIdentity
    assert user_identity.principalId == "AWS:AIDAINPONIXQXHT3IKHL2"
    request_parameters = record.requestParameters
    assert str(request_parameters.sourceIPAddress) == "205.255.255.255/32"
    assert record.responseElements.x_amz_request_id == "D82B88E5F771F645"
    assert (
        record.responseElements.x_amz_id_2
        == "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
    )
    s3 = record.s3
    assert s3.s3SchemaVersion == "1.0"
    assert s3.configurationId == "828aa6fc-f7b5-4305-8584-487c791949c1"
    bucket = s3.bucket
    assert bucket.name == "lambda-artifacts-deafc19498e3f2df"
    assert bucket.ownerIdentity.principalId == "A3I5XTEXAMAI3E"
    assert bucket.arn == "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
    assert s3.object.key == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.object.size == 1305107
    assert s3.object.eTag == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.object.versionId is None
    assert s3.object.sequencer == "0C0F6F405D6ED209E1"
    assert record.glacierEventData is None


@event_parser(model=S3Model)
def handle_s3_glacier(event: S3Model, _: LambdaContext):
    records = list(event.Records)
    assert len(records) == 1
    record: S3RecordModel = records[0]
    assert record.eventVersion == "2.1"
    assert record.eventSource == "aws:s3"
    assert record.awsRegion == "us-east-2"
    convert_time = int(round(record.eventTime.timestamp() * 1000))
    assert convert_time == 1567539447192
    assert record.eventName == "ObjectCreated:Put"
    user_identity = record.userIdentity
    assert user_identity.principalId == "AWS:AIDAINPONIXQXHT3IKHL2"
    request_parameters = record.requestParameters
    assert str(request_parameters.sourceIPAddress) == "205.255.255.255/32"
    assert record.responseElements.x_amz_request_id == "D82B88E5F771F645"
    assert (
        record.responseElements.x_amz_id_2
        == "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
    )
    s3 = record.s3
    assert s3.s3SchemaVersion == "1.0"
    assert s3.configurationId == "828aa6fc-f7b5-4305-8584-487c791949c1"
    bucket = s3.bucket
    assert bucket.name == "lambda-artifacts-deafc19498e3f2df"
    assert bucket.ownerIdentity.principalId == "A3I5XTEXAMAI3E"
    assert bucket.arn == "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
    assert s3.object.key == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.object.size == 1305107
    assert s3.object.eTag == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.object.versionId is None
    assert s3.object.sequencer == "0C0F6F405D6ED209E1"
    assert record.glacierEventData is not None
    convert_time = int(
        round(record.glacierEventData.restoreEventData.lifecycleRestorationExpiryTime.timestamp() * 1000)
    )
    assert convert_time == 60000
    assert record.glacierEventData.restoreEventData.lifecycleRestoreStorageClass == "standard"


def test_s3_trigger_event():
    event_dict = load_event("s3Event.json")
    handle_s3(event_dict, LambdaContext())


def test_s3_glacier_trigger_event():
    event_dict = load_event("s3EventGlacier.json")
    handle_s3_glacier(event_dict, LambdaContext())


def test_s3_empty_object():
    event_dict = load_event("s3Event.json")
    event_dict["Records"][0]["s3"]["object"]["size"] = 0
    parse(event=event_dict, model=S3Model)


def test_s3_none_object_size_failed_validation():
    event_dict = load_event("s3Event.json")
    event_dict["Records"][0]["s3"]["object"]["size"] = None
    with pytest.raises(ValidationError):
        parse(event=event_dict, model=S3Model)


def test_s3_none_etag_value_failed_validation():
    event_dict = load_event("s3Event.json")
    event_dict["Records"][0]["s3"]["object"]["eTag"] = None
    with pytest.raises(ValidationError):
        parse(event=event_dict, model=S3Model)


def test_s3_eventbridge_notification_object_created_event():
    event_dict = load_event("s3EventBridgeNotificationObjectCreatedEvent.json")
    handle_s3_eventbridge_object_created(event_dict, LambdaContext())


def test_s3_eventbridge_notification_object_created_event_no_envelope():
    event_dict = load_event("s3EventBridgeNotificationObjectCreatedEvent.json")
    handle_s3_eventbridge_object_created_no_envelope(event_dict, LambdaContext())


def test_s3_eventbridge_notification_object_deleted_event():
    event_dict = load_event("s3EventBridgeNotificationObjectDeletedEvent.json")
    handle_s3_eventbridge_object_deleted(event_dict, LambdaContext())


def test_s3_eventbridge_notification_object_deleted_event_no_envelope():
    event_dict = load_event("s3EventBridgeNotificationObjectDeletedEvent.json")
    handle_s3_eventbridge_object_deleted_no_envelope(event_dict, LambdaContext())


def test_s3_eventbridge_notification_object_expired_event():
    event_dict = load_event("s3EventBridgeNotificationObjectExpiredEvent.json")
    handle_s3_eventbridge_object_expired(event_dict, LambdaContext())


def test_s3_eventbridge_notification_object_restore_completed_event():
    event_dict = load_event("s3EventBridgeNotificationObjectRestoreCompletedEvent.json")
    handle_s3_eventbridge_object_restore_completed(event_dict, LambdaContext())


@event_parser(model=S3Model)
def handle_s3_delete_object(event: S3Model, _: LambdaContext):
    records = list(event.Records)
    assert len(records) == 1
    record: S3RecordModel = records[0]
    assert record.eventVersion == "2.1"
    assert record.eventSource == "aws:s3"
    assert record.awsRegion == "us-east-2"
    convert_time = int(round(record.eventTime.timestamp() * 1000))
    assert convert_time == 1567539447192
    assert record.eventName == "ObjectRemoved:Delete"
    user_identity = record.userIdentity
    assert user_identity.principalId == "AWS:AIDAINPONIXQXHT3IKHL2"
    request_parameters = record.requestParameters
    assert str(request_parameters.sourceIPAddress) == "205.255.255.255/32"
    assert record.responseElements.x_amz_request_id == "D82B88E5F771F645"
    assert (
        record.responseElements.x_amz_id_2
        == "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
    )
    s3 = record.s3
    assert s3.s3SchemaVersion == "1.0"
    assert s3.configurationId == "828aa6fc-f7b5-4305-8584-487c791949c1"
    bucket = s3.bucket
    assert bucket.name == "lambda-artifacts-deafc19498e3f2df"
    assert bucket.ownerIdentity.principalId == "A3I5XTEXAMAI3E"
    assert bucket.arn == "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
    assert s3.object.key == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.object.size is None
    assert s3.object.eTag is None
    assert s3.object.versionId is None
    assert s3.object.sequencer == "0C0F6F405D6ED209E1"
    assert record.glacierEventData is None


def test_s3_trigger_event_delete_object():
    event_dict = load_event("s3EventDeleteObject.json")
    handle_s3_delete_object(event_dict, LambdaContext())


@event_parser(model=S3EventNotificationEventBridgeDetailModel, envelope=EventBridgeEnvelope)
def handle_s3_eventbridge_object_created(event: S3EventNotificationEventBridgeDetailModel, _: LambdaContext):
    """
    Tests that the `S3EventNotificationEventBridgeDetailModel` parses events from
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
    """
    bucket_name = "example-bucket"
    deletion_type = None
    destination_access_tier = None
    destination_storage_class = None
    _object: S3EventNotificationObjectModel = event.object
    reason = "PutObject"
    request_id = "57H08PA84AB1JZW0"
    requester = "123456789012"
    restore_expiry_time = None
    source_ip_address = "34.252.34.74"
    source_storage_class = None
    version = "0"

    assert bucket_name == event.bucket.name
    assert deletion_type == event.deletion_type
    assert destination_access_tier == event.destination_access_tier
    assert destination_storage_class == event.destination_storage_class
    assert _object == event.object
    assert reason == event.reason
    assert request_id == event.request_id
    assert requester == event.requester
    assert restore_expiry_time == event.restore_expiry_time
    assert source_ip_address == event.source_ip_address
    assert source_storage_class == event.source_storage_class
    assert version == event.version


@event_parser(model=S3EventNotificationEventBridgeModel)
def handle_s3_eventbridge_object_created_no_envelope(event: S3EventNotificationEventBridgeModel, _: LambdaContext):
    """
    Tests that the `S3EventNotificationEventBridgeDetailModel` parses events from
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
    """

    raw_event = load_event("s3EventBridgeNotificationObjectCreatedEvent.json")

    assert event.version == raw_event["version"]
    assert event.id == raw_event["id"]
    assert event.detail_type == raw_event["detail-type"]
    assert event.source == raw_event["source"]
    assert event.account == raw_event["account"]
    assert event.time == datetime.fromisoformat(raw_event["time"].replace("Z", "+00:00"))
    assert event.region == raw_event["region"]
    assert event.resources == raw_event["resources"]

    assert event.detail.version == raw_event["detail"]["version"]
    assert event.detail.bucket.name == raw_event["detail"]["bucket"]["name"]
    assert event.detail.object.key == raw_event["detail"]["object"]["key"]
    assert event.detail.object.size == raw_event["detail"]["object"]["size"]
    assert event.detail.object.etag == raw_event["detail"]["object"]["etag"]
    assert event.detail.object.sequencer == raw_event["detail"]["object"]["sequencer"]
    assert event.detail.request_id == raw_event["detail"]["request-id"]
    assert event.detail.requester == raw_event["detail"]["requester"]
    assert event.detail.source_ip_address == raw_event["detail"]["source-ip-address"]
    assert event.detail.reason == raw_event["detail"]["reason"]


@event_parser(model=S3EventNotificationEventBridgeDetailModel, envelope=EventBridgeEnvelope)
def handle_s3_eventbridge_object_deleted(event: S3EventNotificationEventBridgeDetailModel, _: LambdaContext):
    """
    Tests that the `S3EventNotificationEventBridgeDetailModel` parses events from
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
    """
    bucket_name = "example-bucket"
    deletion_type = "Delete Marker Created"
    destination_access_tier = None
    destination_storage_class = None
    _object: S3EventNotificationObjectModel = event.object
    reason = "DeleteObject"
    request_id = "0BH729840619AG5K"
    requester = "123456789012"
    restore_expiry_time = None
    source_ip_address = "34.252.34.74"
    source_storage_class = None
    version = "0"

    assert bucket_name == event.bucket.name
    assert deletion_type == event.deletion_type
    assert destination_access_tier == event.destination_access_tier
    assert destination_storage_class == event.destination_storage_class
    assert _object == event.object
    assert reason == event.reason
    assert request_id == event.request_id
    assert requester == event.requester
    assert restore_expiry_time == event.restore_expiry_time
    assert source_ip_address == event.source_ip_address
    assert source_storage_class == event.source_storage_class
    assert version == event.version


@event_parser(model=S3EventNotificationEventBridgeModel)
def handle_s3_eventbridge_object_deleted_no_envelope(event: S3EventNotificationEventBridgeModel, _: LambdaContext):
    """
    Tests that the `S3EventNotificationEventBridgeModel` parses events from
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
    """
    raw_event = load_event("s3EventBridgeNotificationObjectDeletedEvent.json")

    assert event.version == raw_event["version"]
    assert event.id == raw_event["id"]
    assert event.detail_type == raw_event["detail-type"]
    assert event.source == raw_event["source"]
    assert event.account == raw_event["account"]
    assert event.time == datetime.fromisoformat(raw_event["time"].replace("Z", "+00:00"))
    assert event.region == raw_event["region"]
    assert event.resources == raw_event["resources"]

    assert event.detail.version == raw_event["detail"]["version"]
    assert event.detail.bucket.name == raw_event["detail"]["bucket"]["name"]
    assert event.detail.object.key == raw_event["detail"]["object"]["key"]
    assert event.detail.object.size == raw_event["detail"]["object"]["size"]
    assert event.detail.object.etag == raw_event["detail"]["object"]["etag"]
    assert event.detail.object.sequencer == raw_event["detail"]["object"]["sequencer"]
    assert event.detail.request_id == raw_event["detail"]["request-id"]
    assert event.detail.requester == raw_event["detail"]["requester"]
    assert event.detail.source_ip_address == raw_event["detail"]["source-ip-address"]
    assert event.detail.reason == raw_event["detail"]["reason"]
    assert event.detail.deletion_type == raw_event["detail"]["deletion-type"]


@event_parser(model=S3EventNotificationEventBridgeDetailModel, envelope=EventBridgeEnvelope)
def handle_s3_eventbridge_object_expired(event: S3EventNotificationEventBridgeDetailModel, _: LambdaContext):
    """
    Tests that the `S3EventNotificationEventBridgeDetailModel` parses events from
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
    """
    bucket_name = "example-bucket"
    deletion_type = "Delete Marker Created"
    destination_access_tier = None
    destination_storage_class = None
    _object: S3EventNotificationObjectModel = event.object
    reason = "Lifecycle Expiration"
    request_id = "20EB74C14654DC47"
    requester = "s3.amazonaws.com"
    restore_expiry_time = None
    source_ip_address = None
    source_storage_class = None
    version = "0"

    assert bucket_name == event.bucket.name
    assert deletion_type == event.deletion_type
    assert destination_access_tier == event.destination_access_tier
    assert destination_storage_class == event.destination_storage_class
    assert _object == event.object
    assert reason == event.reason
    assert request_id == event.request_id
    assert requester == event.requester
    assert restore_expiry_time == event.restore_expiry_time
    assert source_ip_address == event.source_ip_address
    assert source_storage_class == event.source_storage_class
    assert version == event.version


@event_parser(model=S3EventNotificationEventBridgeDetailModel, envelope=EventBridgeEnvelope)
def handle_s3_eventbridge_object_restore_completed(event: S3EventNotificationEventBridgeDetailModel, _: LambdaContext):
    """
    Tests that the `S3EventNotificationEventBridgeDetailModel` parses events from
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
    """
    bucket_name = "example-bucket"
    deletion_type = None
    destination_access_tier = None
    destination_storage_class = None
    _object: S3EventNotificationObjectModel = event.object
    reason = None
    request_id = "189F19CB7FB1B6A4"
    requester = "s3.amazonaws.com"
    restore_expiry_time = "2021-11-13T00:00:00Z"
    source_ip_address = None
    source_storage_class = "GLACIER"
    version = "0"

    assert bucket_name == event.bucket.name
    assert deletion_type == event.deletion_type
    assert destination_access_tier == event.destination_access_tier
    assert destination_storage_class == event.destination_storage_class
    assert _object == event.object
    assert reason == event.reason
    assert request_id == event.request_id
    assert requester == event.requester
    assert restore_expiry_time == event.restore_expiry_time
    assert source_ip_address == event.source_ip_address
    assert source_storage_class == event.source_storage_class
    assert version == event.version
