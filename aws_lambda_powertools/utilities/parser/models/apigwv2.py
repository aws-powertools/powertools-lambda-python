from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic.networks import IPvAnyNetwork

from aws_lambda_powertools.utilities.parser.functions import _validate_source_ip


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
    sourceIp: IPvAnyNetwork | str
    userAgent: str

    @field_validator("sourceIp", mode="before")
    @classmethod
    def _validate_source_ip(cls, value):
        return _validate_source_ip(value=value)


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
    isBase64Encoded: bool | None = None


class ApiGatewayAuthorizerRequestV2(APIGatewayProxyEventV2Model):
    type: Literal["REQUEST"]
    routeArn: str
    identitySource: list[str] | None = None
