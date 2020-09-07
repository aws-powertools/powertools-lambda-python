from typing import Dict, Iterator, Optional


class S3Identity(dict):
    @property
    def principal_id(self) -> str:
        return self["principalId"]


class S3RequestParameters(dict):
    @property
    def source_ip_address(self) -> str:
        return self["sourceIPAddress"]


class S3Bucket(dict):
    @property
    def name(self) -> str:
        return self["name"]

    @property
    def owner_identity(self) -> S3Identity:
        return S3Identity(self["ownerIdentity"])

    @property
    def arn(self) -> str:
        return self["arn"]


class S3Object(dict):
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
        """object eTag"""
        return self["eTag"]

    @property
    def version_id(self) -> Optional[str]:
        """Object version if bucket is versioning-enabled, otherwise null"""
        return self.get("versionId")

    @property
    def sequencer(self) -> str:
        """A string representation of a hexadecimal value used to determine event sequence,
        only used with PUTs and DELETEs
        """
        return self["sequencer"]


class S3Message(dict):
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
    def s3_object(self) -> S3Object:
        """Get the `object` property as an S3Object"""
        return S3Object(self["object"])


class S3EventRecordGlacierRestoreEventData(dict):
    @property
    def lifecycle_restoration_expiry_time(self) -> str:
        return self["lifecycleRestorationExpiryTime"]

    @property
    def lifecycle_restore_storage_class(self) -> str:
        return self["lifecycleRestoreStorageClass"]


class S3EventRecordGlacierEventData(dict):
    @property
    def restore_event_data(self) -> S3EventRecordGlacierRestoreEventData:
        """The restoreEventData key contains attributes related to your restore request."""
        return S3EventRecordGlacierRestoreEventData(self["restoreEventData"])


class S3EventRecord(dict):
    @property
    def event_version(self) -> str:
        """The eventVersion key value contains a major and minor version in the form <major>.<minor>."""
        return self["eventVersion"]

    @property
    def event_source(self) -> str:
        """aws:s3"""
        return self["eventSource"]

    @property
    def aws_region(self) -> str:
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
    def response_elements(self) -> Dict[str, str]:
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
    def glacier_event_data(self) -> Optional[S3EventRecordGlacierEventData]:
        """The glacierEventData key is only visible for s3:ObjectRestore:Completed events."""
        item = self.get("glacierEventData")
        return None if item is None else S3EventRecordGlacierEventData(item)


class S3Event(dict):
    """S3 event notification

    Documentation:
        https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html
        https://docs.aws.amazon.com/AmazonS3/latest/dev/NotificationHowTo.html
        https://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
    """

    @property
    def records(self) -> Iterator[S3EventRecord]:
        for record in self["Records"]:
            yield S3EventRecord(record)
