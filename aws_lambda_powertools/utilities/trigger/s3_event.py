from typing import Any, Dict, Iterator, Optional


class S3Identity:
    def __init__(self, s3_identity: Dict[str, str]):
        self._v = s3_identity

    @property
    def principal_id(self) -> str:
        return self._v["principalId"]


class S3RequestParameters:
    def __init__(self, record: Dict[str, Any]):
        self._v = record

    @property
    def source_ip_address(self) -> str:
        return self._v["requestParameters"]["sourceIPAddress"]


class S3Bucket:
    def __init__(self, record: Dict[str, Any]):
        self._v = record

    @property
    def name(self) -> str:
        return self._v["s3"]["bucket"]["name"]

    @property
    def owner_identity(self) -> S3Identity:
        return S3Identity(self._v["s3"]["bucket"]["ownerIdentity"])

    @property
    def arn(self) -> str:
        return self._v["s3"]["bucket"]["arn"]


class S3Object:
    def __init__(self, record: Dict[str, Any]):
        self._v = record

    @property
    def key(self) -> str:
        """Object key"""
        return self._v["s3"]["object"]["key"]

    @property
    def size(self) -> int:
        """Object byte size"""
        return int(self._v["s3"]["object"]["size"])

    @property
    def etag(self) -> str:
        """object eTag"""
        return self._v["s3"]["object"]["eTag"]

    @property
    def version_id(self) -> Optional[str]:
        """Object version if bucket is versioning-enabled, otherwise null"""
        return self._v["s3"]["object"].get("versionId")

    @property
    def sequencer(self) -> str:
        """A string representation of a hexadecimal value used to determine event sequence,
        only used with PUTs and DELETEs
        """
        return self._v["s3"]["object"]["sequencer"]


class S3Message:
    def __init__(self, record: Dict[str, Any]):
        self._v = record

    @property
    def s3_schema_version(self) -> str:
        return self._v["s3"]["s3SchemaVersion"]

    @property
    def configuration_id(self) -> str:
        """ID found in the bucket notification configuration"""
        return self._v["s3"]["configurationId"]

    @property
    def bucket(self) -> S3Bucket:
        return S3Bucket(self._v)

    @property
    def get_object(self) -> S3Object:
        """Get the `object` property as an S3Object"""
        # Note: this name conflicts with existing python builtins
        return S3Object(self._v)


class S3EventRecordGlacierRestoreEventData:
    def __init__(self, glacier_event_data: Dict[str, Any]):
        self._v = glacier_event_data

    @property
    def lifecycle_restoration_expiry_time(self) -> str:
        """Time when the object restoration will be expired."""
        return self._v["restoreEventData"]["lifecycleRestorationExpiryTime"]

    @property
    def lifecycle_restore_storage_class(self) -> str:
        """Source storage class for restore"""
        return self._v["restoreEventData"]["lifecycleRestoreStorageClass"]


class S3EventRecordGlacierEventData:
    def __init__(self, glacier_event_data: Dict[str, Any]):
        self._v = glacier_event_data

    @property
    def restore_event_data(self) -> S3EventRecordGlacierRestoreEventData:
        """The restoreEventData key contains attributes related to your restore request.

        The glacierEventData key is only visible for s3:ObjectRestore:Completed events
        """
        return S3EventRecordGlacierRestoreEventData(self._v)


class S3EventRecord:
    def __init__(self, record: Dict[str, Any]):
        self._v = record

    @property
    def event_version(self) -> str:
        """The eventVersion key value contains a major and minor version in the form <major>.<minor>."""
        return self._v["eventVersion"]

    @property
    def event_source(self) -> str:
        """The AWS service from which the S3 event originated. For S3, this is aws:s3"""
        return self._v["eventSource"]

    @property
    def aws_region(self) -> str:
        """aws region eg: us-east-1"""
        return self._v["awsRegion"]

    @property
    def event_time(self) -> str:
        """The time, in ISO-8601 format, for example, 1970-01-01T00:00:00.000Z, when S3 finished
        processing the request"""
        return self._v["eventTime"]

    @property
    def event_name(self) -> str:
        """Event type"""
        return self._v["eventName"]

    @property
    def user_identity(self) -> S3Identity:
        return S3Identity(self._v["userIdentity"])

    @property
    def request_parameters(self) -> S3RequestParameters:
        return S3RequestParameters(self._v)

    @property
    def response_elements(self) -> Dict[str, str]:
        """The responseElements key value is useful if you want to trace a request by following up with AWS Support.

        Both x-amz-request-id and x-amz-id-2 help Amazon S3 trace an individual request. These values are the same
        as those that Amazon S3 returns in the response to the request that initiates the events, so they can be
        used to match the event to the request.
        """
        return self._v["responseElements"]

    @property
    def s3(self) -> S3Message:
        return S3Message(self._v)

    @property
    def glacier_event_data(self) -> Optional[S3EventRecordGlacierEventData]:
        """The glacierEventData key is only visible for s3:ObjectRestore:Completed events."""
        item = self._v.get("glacierEventData")
        return None if item is None else S3EventRecordGlacierEventData(item)


class S3Event(dict):
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
