from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyNetwork


class RequestContextV2AuthorizerIamCognito(BaseModel):
    amr: List[str]
    identityId: str
    identityPoolId: str


class RequestContextV2AuthorizerIam(BaseModel):
    accessKey: Optional[str] = None
    accountId: Optional[str] = None
    callerId: Optional[str] = None
    principalOrgId: Optional[str] = None
    userArn: Optional[str] = None
    userId: Optional[str] = None
    cognitoIdentity: Optional[RequestContextV2AuthorizerIamCognito] = None


class RequestContextV2AuthorizerJwt(BaseModel):
    claims: Dict[str, Any]
    scopes: Optional[List[str]] = None


class RequestContextV2Authorizer(BaseModel):
    jwt: Optional[RequestContextV2AuthorizerJwt] = None
    iam: Optional[RequestContextV2AuthorizerIam] = None
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
    authorizer: Optional[RequestContextV2Authorizer] = None
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
    cookies: Optional[List[str]] = None
    headers: Dict[str, str]
    queryStringParameters: Optional[Dict[str, str]] = None
    pathParameters: Optional[Dict[str, str]] = None
    stageVariables: Optional[Dict[str, str]] = None
    requestContext: RequestContextV2
    body: Optional[Union[str, Type[BaseModel]]] = None
    isBase64Encoded: Optional[bool] = None


class ApiGatewayAuthorizerRequestV2(APIGatewayProxyEventV2Model):
    type: Literal["REQUEST"]
    routeArn: str
    identitySource: Optional[List[str]] = None
