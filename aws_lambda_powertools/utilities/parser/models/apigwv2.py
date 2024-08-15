from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyNetwork  # noqa: TCH002


class RequestContextV2AuthorizerIamCognito(BaseModel):
    amr: list[str]
    identityId: str
    identityPoolId: str


class RequestContextV2AuthorizerIam(BaseModel):
    accessKey: str | None = None
    accountId: str | None = None
    callerId: str | None = None
    principalOrgId: str | None = None
    userArn: str | None = None
    userId: str | None = None
    cognitoIdentity: RequestContextV2AuthorizerIamCognito | None = None


class RequestContextV2AuthorizerJwt(BaseModel):
    claims: dict[str, Any]
    scopes: list[str] | None = None


class RequestContextV2Authorizer(BaseModel):
    jwt: RequestContextV2AuthorizerJwt | None = None
    iam: RequestContextV2AuthorizerIam | None = None
    lambda_value: dict[str, Any] | None = Field(None, alias="lambda")


class RequestContextV2Http(BaseModel):
    method: Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    path: str
    protocol: str
    sourceIp: IPvAnyNetwork
    userAgent: str


class RequestContextV2(BaseModel):
    accountId: str
    apiId: str
    authorizer: RequestContextV2Authorizer | None = None
    domainName: str
    domainPrefix: str
    requestId: str
    routeKey: str
    stage: str
    time: str
    timeEpoch: datetime
    http: RequestContextV2Http


class APIGatewayProxyEventV2Model(BaseModel):
    version: str
    routeKey: str
    rawPath: str
    rawQueryString: str
    cookies: list[str] | None = None
    headers: dict[str, str]
    queryStringParameters: dict[str, str] | None = None
    pathParameters: dict[str, str] | None = None
    stageVariables: dict[str, str] | None = None
    requestContext: RequestContextV2
    body: str | type[BaseModel] | None = None
    isBase64Encoded: bool
