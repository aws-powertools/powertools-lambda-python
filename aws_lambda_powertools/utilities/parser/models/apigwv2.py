from datetime import datetime
from typing import Any, Dict, List, Literal, Type, Union

from pydantic import BaseModel, Field, field_validator
from pydantic.networks import IPvAnyNetwork

from aws_lambda_powertools.utilities.parser.functions import _validate_source_ip


class RequestContextV2AuthorizerIamCognito(BaseModel):
    amr: List[str]
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
    claims: Dict[str, Any]
    scopes: List[str] | None = None


class RequestContextV2Authorizer(BaseModel):
    jwt: RequestContextV2AuthorizerJwt | None = None
    iam: RequestContextV2AuthorizerIam | None = None
    lambda_value: Dict[str, Any] | None = Field(None, alias="lambda")


class RequestContextV2Http(BaseModel):
    method: Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    path: str
    protocol: str
    sourceIp: Union[IPvAnyNetwork, str]
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
    cookies: List[str] | None = None
    headers: Dict[str, str]
    queryStringParameters: Dict[str, str] | None = None
    pathParameters: Dict[str, str] | None = None
    stageVariables: Dict[str, str] | None = None
    requestContext: RequestContextV2
    body: Union[str, Type[BaseModel]] | None = None
    isBase64Encoded: bool | None = None


class ApiGatewayAuthorizerRequestV2(APIGatewayProxyEventV2Model):
    type: Literal["REQUEST"]
    routeArn: str
    identitySource: List[str] | None = None
