from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, root_validator
from pydantic.fields import Field
from pydantic.networks import IPvAnyNetwork
from pydantic.types import NonNegativeFloat

from aws_lambda_powertools.utilities.parser.types import Literal


class S3EventRecordGlacierRestoreEventData(BaseModel):
    lifecycleRestorationExpiryTime: datetime
    lifecycleRestoreStorageClass: str


class S3EventRecordGlacierEventData(BaseModel):
    restoreEventData: S3EventRecordGlacierRestoreEventData


class S3Identity(BaseModel):
    principalId: str


class S3RequestParameters(BaseModel):
    sourceIPAddress: IPvAnyNetwork


class S3ResponseElements(BaseModel):
    x_amz_request_id: str = Field(None, alias="x-amz-request-id")
    x_amz_id_2: str = Field(None, alias="x-amz-id-2")


class S3OwnerIdentify(BaseModel):
    principalId: str


class S3Bucket(BaseModel):
    name: str
    ownerIdentity: S3OwnerIdentify
    arn: str


class S3Object(BaseModel):
    key: str
    size: Optional[NonNegativeFloat]
    eTag: Optional[str]
    sequencer: str
    versionId: Optional[str]


class S3Message(BaseModel):
    s3SchemaVersion: str
    configurationId: str
    bucket: S3Bucket
    object: S3Object  # noqa: A003,VNE003


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
    glacierEventData: Optional[S3EventRecordGlacierEventData]

    @root_validator
    def validate_s3_object(cls, values):
        event_name = values.get("eventName")
        s3_object = values.get("s3").object
        if "ObjectRemoved" not in event_name:
            if s3_object.size is None or s3_object.eTag is None:
                raise ValueError("S3Object.size and S3Object.eTag are required for non-ObjectRemoved events")
        return values


class S3Model(BaseModel):
    Records: List[S3RecordModel]
