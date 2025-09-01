from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, model_validator
from pydantic.fields import Field
from pydantic.networks import IPvAnyNetwork
from pydantic.types import NonNegativeFloat

from .event_bridge import EventBridgeModel


class S3EventRecordGlacierRestoreEventData(BaseModel):
    lifecycleRestorationExpiryTime: datetime
    lifecycleRestoreStorageClass: str = Field(
        description="Source storage class for restore.",
        examples=[
            "standard",
            "standard_ia",
            "glacier",
        ],
    )


class S3EventRecordGlacierEventData(BaseModel):
    restoreEventData: S3EventRecordGlacierRestoreEventData


class S3Identity(BaseModel):
    principalId: str = Field(
        description="Amazon customer ID of the user who caused the event.",
        examples=[
            "AIDAJDPLRKLG7UEXAMPLE",
            "A1YQ72UWCM96UF",
            "AWS:AIDAINPONIXQXHT3IKHL2",
        ],
    )


class S3RequestParameters(BaseModel):
    sourceIPAddress: Union[IPvAnyNetwork, Literal["s3.amazonaws.com"]]


class S3ResponseElements(BaseModel):
    x_amz_request_id: str = Field(
        ...,
        alias="x-amz-request-id",
        description="Amazon S3 generated request ID.",
        examples=[
            "C3D13FE58DE4C810",
            "D82B88E5F771F645",
        ],
    )
    x_amz_id_2: str = Field(
        ...,
        alias="x-amz-id-2",
        description="ID of the Amazon S3 host that processed the request.",
        examples=[
            "FMyUVURIY8/IgAtTv8xRjskZQpcIZ9KG4V5Wp6S7S/JRWeUWerMUE5JgHvANOjpD",
            "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo=",
        ],
    )


class S3OwnerIdentify(BaseModel):
    principalId: str = Field(
        description="Amazon customer ID of the bucket owner.",
        examples=[
            "A3I5XTEXAMAI3E",
            "A1YQ72UWCM96UF",
            "AWS:AIDAINPONIXQXHT3IKHL2",
        ],
    )


class S3Bucket(BaseModel):
    name: str = Field(
        description="Name of the Amazon S3 bucket.",
        examples=[
            "lambda-artifacts-deafc19498e3f2df",
            "example-bucket",
            "sourcebucket",
        ],
    )
    ownerIdentity: S3OwnerIdentify
    arn: str = Field(
        description="The ARN of the Amazon S3 bucket.",
        examples=[
            "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df",
            "arn:aws:s3:::example-bucketarn:aws:s3:::sourcebucket",
        ],
    )


class S3Object(BaseModel):
    key: str = Field(
        description="The object key (file name) of the S3 object.",
        examples=[
            "my-image.jpg",
            "documents/report.pdf",
            "logs/2023/01/15/app.log",
        ],
    )
    size: Optional[NonNegativeFloat] = Field(
        default=None,
        description="The size of the object in bytes.",
        examples=[1024, 2048576, 0],
    )
    eTag: Optional[str] = Field(
        default=None,
        description="The entity tag (ETag) of the object.",
        examples=[
            "d41d8cd98f00b204e9800998ecf8427e",
            "098f6bcd4621d373cade4e832627b4f6",
        ],
    )
    sequencer: Optional[str] = Field(
        default=None,
        description="A string representation of a hexadecimal value used to determine event sequence.",
        examples=[
            "0A1B2C3D4E5F678901",
            "005B21C13A6F24045E",
        ],
    )
    versionId: Optional[str] = Field(
        default=None,
        description="The version ID of the object (if versioning is enabled).",
        examples=[
            "096fKKXTRTtl3on89fVO.nfljtsv6qko",
            "null",
        ],
    )


class S3Message(BaseModel):
    s3SchemaVersion: str = Field(
        description="S3 schema version.",
        examples=[
            "1.0",
        ],
    )
    configurationId: str = Field(
        description="ID of the bucket notification configuration.",
        examples=[
            "828aa6fc-f7b5-4305-8584-487c791949c1",
            "f99fa751-7860-4d65-86cb-10ff34448555",
            "b1d3a482-96eb-4d3a-abd7-763662a6ba94",
        ],
    )
    bucket: S3Bucket
    object: S3Object  # noqa: A003


class S3EventNotificationObjectModel(BaseModel):
    key: str = Field(
        description="The object key (file name) of the S3 object.",
        examples=[
            "my-image.jpg",
            "documents/report.pdf",
            "logs/2023/01/15/app.log",
        ],
    )
    size: Optional[NonNegativeFloat] = Field(
        default=None,
        description="The size of the object in bytes.",
        examples=[1024, 2048576, 0],
    )
    etag: str = Field(
        default="",
        description="The entity tag (ETag) of the object.",
        examples=[
            "d41d8cd98f00b204e9800998ecf8427e",
            "098f6bcd4621d373cade4e832627b4f6",
        ],
    )
    version_id: Optional[str] = Field(
        default=None,
        alias="version-id",
        description="The version ID of the object (if versioning is enabled).",
        examples=[
            "096fKKXTRTtl3on89fVO.nfljtsv6qko",
            "null",
        ],
    )
    sequencer: Optional[str] = Field(
        default=None,
        description="A string representation of a hexadecimal value used to determine event sequence.",
        examples=[
            "0A1B2C3D4E5F678901",
            "005B21C13A6F24045E",
        ],
    )


class S3EventNotificationEventBridgeBucketModel(BaseModel):
    name: str = Field(
        description="Name of the Amazon S3 bucket.",
        examples=[
            "lambda-artifacts-deafc19498e3f2df",
            "example-bucket",
            "sourcebucket",
        ],
    )


class S3EventNotificationEventBridgeDetailModel(BaseModel):
    version: str = Field(
        description="Version of the event message. Currently 0 (zero) for all events",
        examples=[
            "0",
        ],
    )
    bucket: S3EventNotificationEventBridgeBucketModel
    object: S3EventNotificationObjectModel  # noqa: A003
    request_id: str = Field(
        ...,
        alias="request-id",
        description="Amazon S3 generated request ID.",
        examples=[
            "C3D13FE58DE4C810",
            "D82B88E5F771F645",
            "N4N7GDK58NMKJ12R",
        ],
    )
    requester: str = Field(
        description="AWS account ID or AWS service principal of requester, or 's3.amazonaws.com'.",
        examples=[
            "s3.amazonaws.com",
            "123456789012",
        ],
    )
    source_ip_address: Optional[str] = Field(
        None,
        alias="source-ip-address",
        description="Source IP address of S3 request. Only present for events triggered by an S3 request.",
        examples=[
            "0.0.0.0",
            "255.255.255.255",
        ],
    )
    reason: Optional[str] = Field(
        default=None,
        description="For 'Object Created' events, the S3 API used to create the object: PutObject, POST Object, "
        "CopyObject, or CompleteMultipartUpload. For 'Object Deleted' events, this is set to 'DeleteObject' "
        "when an object is deleted by an S3 API call, or 'Lifecycle Expiration' when an object is deleted by an "
        "S3 Lifecycle expiration rule. For more information, see https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html",
        examples=[
            "Lifecycle Expiration",
            "PutObject",
            "DeleteObject",
        ],
    )
    deletion_type: Optional[str] = Field(
        default=None,
        alias="deletion-type",
        description="For 'Object Deleted' events, when an unversioned object is deleted, or a versioned object is "
        "permanently deleted, this is set to 'Permanently Deleted'. When a delete marker is created for a "
        "versioned object, this is set to 'Delete Marker Created'. For more information, "
        "see https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeletingObjectVersions.html",
        examples=["Delete Marker Created", "Permanently Deleted"],
    )
    restore_expiry_time: Optional[str] = Field(
        default=None,
        alias="restore-expiry-time",
        description="For 'Object Restore Completed' events, the time when the temporary copy of the object will be "
        "deleted from S3. For more information, see https://docs.aws.amazon.com/AmazonS3/latest/userguide/archived-objects.html.",
        examples=["2021-11-13T00:00:00Z"],
    )
    source_storage_class: Optional[str] = Field(
        default=None,
        alias="source-storage-class",
        description="For 'Object Restore Initiated' and 'Object Restore Completed' events, the storage class of the "
        "object being restored. For more information, see https://docs.aws.amazon.com/AmazonS3/latest/userguide/archived-objects.html.",
        examples=["GLACIER", "STANDARD", "STANDARD_IA"],
    )
    destination_storage_class: Optional[str] = Field(
        default=None,
        alias="destination-storage-class",
        description="For 'Object Storage Class Changed' events, the new storage class of the object. For more "
        "information, see https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html.",
        examples=["INTELLIGENT_TIERING", "STANDARD", "STANDARD_IA"],
    )
    destination_access_tier: Optional[str] = Field(
        default=None,
        alias="destination-access-tier",
        description="For 'Object Access Tier Changed' events, the new access tier of the object. For more information, "
        "see https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html.",
        examples=["DEEP_ARCHIVE_ACCESS", "ARCHIVE_ACCESS"],
    )


class S3EventNotificationEventBridgeModel(EventBridgeModel):  # type: ignore[override]
    detail: S3EventNotificationEventBridgeDetailModel


class S3RecordModel(BaseModel):
    eventVersion: str = Field(
        description="Version of the event message, with a major and minor version in the form <major>.<minor>.",
        examples=[
            "2.2",
            "1.9",
        ],
    )
    eventSource: Literal["aws:s3"]
    awsRegion: str = Field(
        description="The AWS region where the event occurred.",
        examples=[
            "us-east-1",
            "eu-central-1",
            "ap-northeast-2",
        ],
    )
    eventTime: datetime = Field(
        description="The time, in ISO-8601 format, for example, 1970-01-01T00:00:00.000Z, when Amazon S3 finished "
        "processing the request.",
        examples=[
            "1970-01-01T00:00:00.000Z",
        ],
    )
    eventName: str = Field(
        description="Name of the event notification type, without the 's3:' prefix. See more https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-event-types-and-destinations.html.",
        examples=[
            "ObjectCreated",
            "ObjectCreated:Put",
            "LifecycleExpiration:Delete",
        ],
    )
    userIdentity: S3Identity
    requestParameters: S3RequestParameters
    responseElements: S3ResponseElements
    s3: S3Message
    glacierEventData: Optional[S3EventRecordGlacierEventData] = None

    @model_validator(mode="before")
    def validate_s3_object(cls, values):
        event_name = values.get("eventName")
        s3_object = values.get("s3").get("object")
        if ":Delete" not in event_name and (s3_object.get("size") is None or s3_object.get("eTag") is None):
            raise ValueError(
                "Size and eTag fields are required for all events except ObjectRemoved:* and LifecycleExpiration:*.",
            )
        return values


class S3Model(BaseModel):
    Records: List[S3RecordModel]
