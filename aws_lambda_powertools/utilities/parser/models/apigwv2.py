from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyNetwork

from ..types import Literal


class RequestContextV2AuthorizerIamCognito(BaseModel):
    amr: List[str]
    identityId: str
    identityPoolId: str


class RequestContextV2AuthorizerIam(BaseModel):
    accessKey: Optional[str]
    accountId: Optional[str]
    callerId: Optional[str]
    principalOrgId: Optional[str]
    userArn: Optional[str]
    userId: Optional[str]
    cognitoIdentity: RequestContextV2AuthorizerIamCognito


class RequestContextV2AuthorizerJwt(BaseModel):
    claims: Dict[str, Any]
    scopes: List[str]


class RequestContextV2Authorizer(BaseModel):
    jwt: Optional[RequestContextV2AuthorizerJwt]
    iam: Optional[RequestContextV2AuthorizerIam]
    lambda_value: Optional[Dict[str, Any]] = Field(None, alias="lambda")


class RequestContextV2Http(BaseModel):
    method: Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    path: str
    protocol: str
    sourceIp: IPvAnyNetwork
    userAgent: str


class RequestContextV2(BaseModel):
    accountId: str
    apiId: str
    authorizer: Optional[RequestContextV2Authorizer]
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
    cookies: Optional[List[str]]
    headers: Dict[str, str]
    queryStringParameters: Dict[str, str]
    pathParameters: Optional[Dict[str, str]]
    stageVariables: Optional[Dict[str, str]]
    requestContext: RequestContextV2
    body: str
    isBase64Encoded: bool
