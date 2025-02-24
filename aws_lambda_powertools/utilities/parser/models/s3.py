from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, model_validator
from pydantic.fields import Field
from pydantic.networks import IPvAnyNetwork
from pydantic.types import NonNegativeFloat

from .event_bridge import EventBridgeModel


class S3EventRecordGlacierRestoreEventData(BaseModel):
    lifecycleRestorationExpiryTime: datetime
    lifecycleRestoreStorageClass: str


class S3EventRecordGlacierEventData(BaseModel):
    restoreEventData: S3EventRecordGlacierRestoreEventData


class S3Identity(BaseModel):
    principalId: str


class S3RequestParameters(BaseModel):
    sourceIPAddress: Union[IPvAnyNetwork, Literal["s3.amazonaws.com"]]


class S3ResponseElements(BaseModel):
    x_amz_request_id: str = Field(..., alias="x-amz-request-id")
    x_amz_id_2: str = Field(..., alias="x-amz-id-2")


class S3OwnerIdentify(BaseModel):
    principalId: str


class S3Bucket(BaseModel):
    name: str
    ownerIdentity: S3OwnerIdentify
    arn: str


class S3Object(BaseModel):
    key: str
    size: Optional[NonNegativeFloat] = None
    eTag: Optional[str] = None
    sequencer: Optional[str] = None
    versionId: Optional[str] = None


class S3Message(BaseModel):
    s3SchemaVersion: str
    configurationId: str
    bucket: S3Bucket
    object: S3Object  # noqa: A003,VNE003


class S3EventNotificationObjectModel(BaseModel):
    key: str
    size: Optional[NonNegativeFloat] = None
    etag: str = Field(default="")
    version_id: Optional[str] = Field(None, alias="version-id")
    sequencer: Optional[str] = None


class S3EventNotificationEventBridgeBucketModel(BaseModel):
    name: str


class S3EventNotificationEventBridgeDetailModel(BaseModel):
    version: str
    bucket: S3EventNotificationEventBridgeBucketModel
    object: S3EventNotificationObjectModel  # noqa: A003,VNE003
    request_id: str = Field(..., alias="request-id")
    requester: str
    source_ip_address: Optional[str] = Field(None, alias="source-ip-address")
    reason: Optional[str] = None
    deletion_type: Optional[str] = Field(None, alias="deletion-type")
    restore_expiry_time: Optional[str] = Field(None, alias="restore-expiry-time")
    source_storage_class: Optional[str] = Field(None, alias="source-storage-class")
    destination_storage_class: Optional[str] = Field(None, alias="destination-storage-class")
    destination_access_tier: Optional[str] = Field(None, alias="destination-access-tier")


class S3EventNotificationEventBridgeModel(EventBridgeModel):  # type: ignore[override]
    detail: S3EventNotificationEventBridgeDetailModel


class S3RecordModel(BaseModel):
    eventVersion: str
    eventSource: Literal["aws:s3"]
    awsRegion: str
    eventTime: datetime
    eventName: str
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
