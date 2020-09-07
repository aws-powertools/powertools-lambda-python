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
        return self["key"]

    @property
    def size(self) -> int:
        return int(self["size"])

    @property
    def etag(self) -> str:
        return self["eTag"]

    @property
    def version_id(self) -> Optional[str]:
        return self.get("versionId")

    @property
    def sequencer(self) -> str:
        return self["sequencer"]


class S3Message(dict):
    @property
    def s3_schema_version(self) -> str:
        return self["s3SchemaVersion"]

    @property
    def configuration_id(self) -> str:
        return self["configurationId"]

    @property
    def bucket(self) -> S3Bucket:
        return S3Bucket(self["bucket"])

    @property
    def object(self) -> S3Object:  # noqa: A003
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
        return S3EventRecordGlacierRestoreEventData(self["restoreEventData"])


class S3EventRecord(dict):
    @property
    def event_version(self) -> str:
        return self["eventVersion"]

    @property
    def event_source(self) -> str:
        return self["eventSource"]

    @property
    def aws_region(self) -> str:
        return self["awsRegion"]

    @property
    def event_time(self) -> str:
        return self["eventTime"]

    @property
    def event_name(self) -> str:
        return self["eventName"]

    @property
    def user_identity(self) -> S3Identity:
        return S3Identity(self["userIdentity"])

    @property
    def request_parameters(self) -> S3RequestParameters:
        return S3RequestParameters(self["requestParameters"])

    @property
    def response_elements(self) -> Dict[str, str]:
        return self["responseElements"]

    @property
    def s3(self) -> S3Message:
        return S3Message(self["s3"])

    @property
    def glacier_event_data(self) -> Optional[S3EventRecordGlacierEventData]:
        item = self.get("glacierEventData")
        return None if item is None else S3EventRecordGlacierEventData(item)


class S3Event(dict):
    @property
    def records(self) -> Iterator[S3EventRecord]:
        for record in self["Records"]:
            yield S3EventRecord(record)
