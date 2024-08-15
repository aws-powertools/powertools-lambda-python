from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Any, Literal

from pydantic import BaseModel, model_validator
from pydantic.networks import IPvAnyNetwork  # noqa: TCH002


class ApiGatewayUserCertValidity(BaseModel):
    notBefore: str
    notAfter: str


class ApiGatewayUserCert(BaseModel):
    clientCertPem: str
    subjectDN: str
    issuerDN: str
    serialNumber: str
    validity: ApiGatewayUserCertValidity


class APIGatewayEventIdentity(BaseModel):
    accessKey: str | None = None
    accountId: str | None = None
    apiKey: str | None = None
    apiKeyId: str | None = None
    caller: str | None = None
    cognitoAuthenticationProvider: str | None = None
    cognitoAuthenticationType: str | None = None
    cognitoIdentityId: str | None = None
    cognitoIdentityPoolId: str | None = None
    principalOrgId: str | None = None
    # see #1562, temp workaround until API Gateway fixes it the Test button payload
    # removing it will not be considered a regression in the future
    sourceIp: IPvAnyNetwork | Literal["test-invoke-source-ip"]
    user: str | None = None
    userAgent: str | None = None
    userArn: str | None = None
    clientCert: ApiGatewayUserCert | None = None


class APIGatewayEventAuthorizer(BaseModel):
    claims: dict[str, Any] | None = None
    scopes: list[str] | None = None


class APIGatewayEventRequestContext(BaseModel):
    accountId: str
    apiId: str
    authorizer: APIGatewayEventAuthorizer | None = None
    stage: str
    protocol: str
    identity: APIGatewayEventIdentity
    requestId: str
    requestTime: str
    requestTimeEpoch: datetime
    resourceId: str | None = None
    resourcePath: str
    domainName: str | None = None
    domainPrefix: str | None = None
    extendedRequestId: str | None = None
    httpMethod: Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    path: str
    connectedAt: datetime | None = None
    connectionId: str | None = None
    eventType: Literal["CONNECT", "MESSAGE", "DISCONNECT"] | None = None
    messageDirection: str | None = None
    messageId: str | None = None
    routeKey: str | None = None
    operationName: str | None = None

    @model_validator(mode="before")
    def check_message_id(cls, values):
        message_id, event_type = values.get("messageId"), values.get("eventType")
        if message_id is not None and event_type != "MESSAGE":
            raise ValueError("messageId is available only when the `eventType` is `MESSAGE`")
        return values


class APIGatewayProxyEventModel(BaseModel):
    version: str | None = None
    resource: str
    path: str
    httpMethod: Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    headers: dict[str, str]
    multiValueHeaders: dict[str, list[str]]
    queryStringParameters: dict[str, str] | None = None
    multiValueQueryStringParameters: dict[str, list[str]] | None = None
    requestContext: APIGatewayEventRequestContext
    pathParameters: dict[str, str] | None = None
    stageVariables: dict[str, str] | None = None
    isBase64Encoded: bool
    body: str | type[BaseModel] | None = None
