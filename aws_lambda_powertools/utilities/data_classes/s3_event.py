from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import unquote_plus

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper
from aws_lambda_powertools.utilities.data_classes.event_bridge_event import (
    EventBridgeEvent,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


class S3Identity(DictWrapper):
    @property
    def principal_id(self) -> str:
        return self["principalId"]


class S3RequestParameters(DictWrapper):
    @property
    def source_ip_address(self) -> str:
        return self["sourceIPAddress"]


class S3EventNotificationEventBridgeBucket(DictWrapper):
    @property
    def name(self) -> str:
        return self["name"]


class S3EventBridgeNotificationObject(DictWrapper):
    @property
    def key(self) -> str:
        """Object key"""
        return unquote_plus(self["key"])

    @property
    def size(self) -> int | None:
        """Object size. Object deletion event doesn't contain size."""
        return self.get("size")

    @property
    def etag(self) -> str:
        """Object eTag. Object deletion event doesn't contain eTag; we default to empty string"""
        return self.get("etag") or ""

    @property
    def version_id(self) -> str:
        """Object version ID"""
        return self["version-id"]

    @property
    def sequencer(self) -> str:
        """Object key"""
        return self["sequencer"]


class S3EventBridgeNotificationDetail(DictWrapper):
    @property
    def version(self) -> str:
        """Get the detail version"""
        return self["version"]

    @property
    def bucket(self) -> S3EventNotificationEventBridgeBucket:
        """Get the bucket name for the S3 notification"""
        return S3EventNotificationEventBridgeBucket(self["bucket"])

    @property
    def object(self) -> S3EventBridgeNotificationObject:  # noqa: A003 # ignore shadowing built-in grammar
        """Get the request-id for the S3 notification"""
        return S3EventBridgeNotificationObject(self["object"])

    @property
    def request_id(self) -> str:
        """Get the request-id for the S3 notification"""
        return self["request-id"]

    @property
    def requester(self) -> str:
        """Get the AWS account ID or AWS service principal of requester for the S3 notification"""
        return self["requester"]

    @property
    def source_ip_address(self) -> str | None:
        """Get the source IP address of S3 request. Only present for events triggered by an S3 request."""
        return self.get("source-ip-address")

    @property
    def reason(self) -> str | None:
        """Get the reason for the S3 notification.

        For 'Object Created events', the S3 API used to create the object: `PutObject`, `POST Object`, `CopyObject`, or
        `CompleteMultipartUpload`. For 'Object Deleted' events, this is set to `DeleteObject` when an object is deleted
        by an S3 API call, or 'Lifecycle Expiration' when an object is deleted by an S3 Lifecycle expiration rule.
        """
        return self.get("reason")

    @property
    def deletion_type(self) -> str | None:
        """Get the deletion type for the S3 object in this notification.

        For 'Object Deleted' events, when an unversioned object is deleted, or a versioned object is permanently deleted
        this is set to 'Permanently Deleted'. When a delete marker is created for a versioned object, this is set to
        'Delete Marker Created'.
        """
        return self.get("deletion-type")

    @property
    def restore_expiry_time(self) -> str | None:
        """Get the restore expiry time for the S3 object in this notification.

        For 'Object Restore Completed' events, the time when the temporary copy of the object will be deleted from S3.
        """
        return self.get("restore-expiry-time")

    @property
    def source_storage_class(self) -> str | None:
        """Get the source storage class of the S3 object in this notification.

        For 'Object Restore Initiated' and 'Object Restore Completed' events, the storage class of the object being
        restored.
        """
        return self.get("source-storage-class")

    @property
    def destination_storage_class(self) -> str | None:
        """Get the destination storage class of the S3 object in this notification.

        For 'Object Storage Class Changed' events, the new storage class of the object.
        """
        return self.get("destination-storage-class")

    @property
    def destination_access_tier(self) -> str | None:
        """Get the destination access tier of the S3 object in this notification.

        For 'Object Access Tier Changed' events, the new access tier of the object.
        """
        return self.get("destination-access-tier")


class S3EventBridgeNotificationEvent(EventBridgeEvent):
    """Amazon S3EventBridge Event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
    """

    @property
    def detail(self) -> S3EventBridgeNotificationDetail:  # type: ignore[override]
        """S3 notification details"""
        return S3EventBridgeNotificationDetail(self["detail"])


class S3Bucket(DictWrapper):
    @property
    def name(self) -> str:
        return self["name"]

    @property
    def owner_identity(self) -> S3Identity:
        return S3Identity(self["ownerIdentity"])

    @property
    def arn(self) -> str:
        return self["arn"]


class S3Object(DictWrapper):
    @property
    def key(self) -> str:
        """Object key"""
        return self["key"]

    @property
    def size(self) -> int:
        """Object byte size"""
        return int(self["size"])

    @property
    def etag(self) -> str:
        """Object eTag. Object deletion event doesn't contain eTag; we default to empty string"""
        return self.get("eTag") or ""

    @property
    def version_id(self) -> str | None:
        """Object version if bucket is versioning-enabled, otherwise null"""
        return self.get("versionId")

    @property
    def sequencer(self) -> str:
        """A string representation of a hexadecimal value used to determine event sequence,
        only used with PUTs and DELETEs
        """
        return self["sequencer"]


class S3Message(DictWrapper):
    @property
    def s3_schema_version(self) -> str:
        return self["s3SchemaVersion"]

    @property
    def configuration_id(self) -> str:
        """ID found in the bucket notification configuration"""
        return self["configurationId"]

    @property
    def bucket(self) -> S3Bucket:
        return S3Bucket(self["bucket"])

    @property
    def get_object(self) -> S3Object:
        """Get the `object` property as an S3Object"""
        # Note: this name conflicts with existing python builtins
        return S3Object(self["object"])


class S3EventRecordGlacierRestoreEventData(DictWrapper):
    @property
    def lifecycle_restoration_expiry_time(self) -> str:
        """Time when the object restoration will be expired."""
        return self["lifecycleRestorationExpiryTime"]

    @property
    def lifecycle_restore_storage_class(self) -> str:
        """Source storage class for restore"""
        return self["lifecycleRestoreStorageClass"]


class S3EventRecordGlacierEventData(DictWrapper):
    @property
    def restore_event_data(self) -> S3EventRecordGlacierRestoreEventData:
        """The restoreEventData key contains attributes related to your restore request.

        The glacierEventData key is only visible for s3:ObjectRestore:Completed events
        """
        return S3EventRecordGlacierRestoreEventData(self["restoreEventData"])


class S3EventRecord(DictWrapper):
    @property
    def event_version(self) -> str:
        """The eventVersion key value contains a major and minor version in the form <major>.<minor>."""
        return self["eventVersion"]

    @property
    def event_source(self) -> str:
        """The AWS service from which the S3 event originated. For S3, this is aws:s3"""
        return self["eventSource"]

    @property
    def aws_region(self) -> str:
        """aws region eg: us-east-1"""
        return self["awsRegion"]

    @property
    def event_time(self) -> str:
        """The time, in ISO-8601 format, for example, 1970-01-01T00:00:00.000Z, when S3 finished
        processing the request"""
        return self["eventTime"]

    @property
    def event_name(self) -> str:
        """Event type"""
        return self["eventName"]

    @property
    def user_identity(self) -> S3Identity:
        return S3Identity(self["userIdentity"])

    @property
    def request_parameters(self) -> S3RequestParameters:
        return S3RequestParameters(self["requestParameters"])

    @property
    def response_elements(self) -> dict[str, str]:
        """The responseElements key value is useful if you want to trace a request by following up with AWS Support.

        Both x-amz-request-id and x-amz-id-2 help Amazon S3 trace an individual request. These values are the same
        as those that Amazon S3 returns in the response to the request that initiates the events, so they can be
        used to match the event to the request.
        """
        return self["responseElements"]

    @property
    def s3(self) -> S3Message:
        return S3Message(self["s3"])

    @property
    def glacier_event_data(self) -> S3EventRecordGlacierEventData | None:
        """The glacierEventData key is only visible for s3:ObjectRestore:Completed events."""
        item = self.get("glacierEventData")
        return None if item is None else S3EventRecordGlacierEventData(item)


class S3Event(DictWrapper):
    """S3 event notification

    Documentation:
    -------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html
    - https://docs.aws.amazon.com/AmazonS3/latest/dev/NotificationHowTo.html
    - https://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
    """

    @property
    def records(self) -> Iterator[S3EventRecord]:
        for record in self["Records"]:
            yield S3EventRecord(record)

    @property
    def record(self) -> S3EventRecord:
        """Get the first s3 event record"""
        return next(self.records)

    @property
    def bucket_name(self) -> str:
        """Get the bucket name for the first s3 event record"""
        return self["Records"][0]["s3"]["bucket"]["name"]

    @property
    def object_key(self) -> str:
        """Get the object key for the first s3 event record and unquote plus"""
        return unquote_plus(self["Records"][0]["s3"]["object"]["key"])
