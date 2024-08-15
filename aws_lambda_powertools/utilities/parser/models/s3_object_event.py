from __future__ import annotations

from pydantic import BaseModel, HttpUrl


class S3ObjectContext(BaseModel):
    inputS3Url: HttpUrl
    outputRoute: str
    outputToken: str


class S3ObjectConfiguration(BaseModel):
    accessPointArn: str
    supportingAccessPointArn: str
    payload: str | type[BaseModel]


class S3ObjectUserRequest(BaseModel):
    url: str
    headers: dict[str, str]


class S3ObjectSessionIssuer(BaseModel):
    type: str  # noqa: A003, VNE003
    userName: str | None = None
    principalId: str
    arn: str
    accountId: str


class S3ObjectSessionAttributes(BaseModel):
    creationDate: str
    mfaAuthenticated: bool


class S3ObjectSessionContext(BaseModel):
    sessionIssuer: S3ObjectSessionIssuer
    attributes: S3ObjectSessionAttributes


class S3ObjectUserIdentity(BaseModel):
    type: str  # noqa: A003
    accountId: str
    accessKeyId: str
    userName: str | None = None
    principalId: str
    arn: str
    sessionContext: S3ObjectSessionContext | None = None


class S3ObjectLambdaEvent(BaseModel):
    xAmzRequestId: str
    getObjectContext: S3ObjectContext
    configuration: S3ObjectConfiguration
    userRequest: S3ObjectUserRequest
    userIdentity: S3ObjectUserIdentity
    protocolVersion: str
