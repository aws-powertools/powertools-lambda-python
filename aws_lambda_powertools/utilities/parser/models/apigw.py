from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, root_validator
from pydantic.networks import IPvAnyNetwork

from ..types import Literal


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
    accessKey: Optional[str]
    accountId: Optional[str]
    apiKey: Optional[str]
    apiKeyId: Optional[str]
    caller: Optional[str]
    cognitoAuthenticationProvider: Optional[str]
    cognitoAuthenticationType: Optional[str]
    cognitoIdentityId: Optional[str]
    cognitoIdentityPoolId: Optional[str]
    principalOrgId: Optional[str]
    sourceIp: IPvAnyNetwork
    user: Optional[str]
    userAgent: Optional[str]
    userArn: Optional[str]
    clientCert: Optional[ApiGatewayUserCert]


class APIGatewayEventAuthorizer(BaseModel):
    claims: Optional[Dict[str, Any]]
    scopes: Optional[List[str]]


class APIGatewayEventRequestContext(BaseModel):
    accountId: str
    apiId: str
    authorizer: Optional[APIGatewayEventAuthorizer]
    stage: str
    protocol: str
    identity: APIGatewayEventIdentity
    requestId: str
    requestTime: str
    requestTimeEpoch: datetime
    resourceId: Optional[str]
    resourcePath: str
    domainName: Optional[str]
    domainPrefix: Optional[str]
    extendedRequestId: Optional[str]
    httpMethod: Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    path: str
    connectedAt: Optional[datetime]
    connectionId: Optional[str]
    eventType: Optional[Literal["CONNECT", "MESSAGE", "DISCONNECT"]]
    messageDirection: Optional[str]
    messageId: Optional[str]
    routeKey: Optional[str]
    operationName: Optional[str]

    @root_validator(allow_reuse=True)
    def check_message_id(cls, values):
        message_id, event_type = values.get("messageId"), values.get("eventType")
        if message_id is not None and event_type != "MESSAGE":
            raise TypeError("messageId is available only when the `eventType` is `MESSAGE`")
        return values


class APIGatewayProxyEventModel(BaseModel):
    version: Optional[str]
    resource: str
    path: str
    httpMethod: Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    headers: Dict[str, str]
    multiValueHeaders: Dict[str, List[str]]
    queryStringParameters: Optional[Dict[str, str]]
    multiValueQueryStringParameters: Optional[Dict[str, List[str]]]
    requestContext: APIGatewayEventRequestContext
    pathParameters: Optional[Dict[str, str]]
    stageVariables: Optional[Dict[str, str]]
    isBase64Encoded: bool
    body: str
