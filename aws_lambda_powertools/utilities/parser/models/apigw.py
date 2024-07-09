from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, root_validator
from pydantic.networks import IPvAnyNetwork

from aws_lambda_powertools.utilities.parser.types import Literal


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
    accessKey: Optional[str] = None
    accountId: Optional[str] = None
    apiKey: Optional[str] = None
    apiKeyId: Optional[str] = None
    caller: Optional[str] = None
    cognitoAuthenticationProvider: Optional[str] = None
    cognitoAuthenticationType: Optional[str] = None
    cognitoIdentityId: Optional[str] = None
    cognitoIdentityPoolId: Optional[str] = None
    principalOrgId: Optional[str] = None
    # see #1562, temp workaround until API Gateway fixes it the Test button payload
    # removing it will not be considered a regression in the future
    sourceIp: Union[IPvAnyNetwork, Literal["test-invoke-source-ip"]]
    user: Optional[str] = None
    userAgent: Optional[str] = None
    userArn: Optional[str] = None
    clientCert: Optional[ApiGatewayUserCert] = None


class APIGatewayEventAuthorizer(BaseModel):
    claims: Optional[Dict[str, Any]] = None
    scopes: Optional[List[str]] = None


class APIGatewayEventRequestContext(BaseModel):
    accountId: str
    apiId: str
    authorizer: Optional[APIGatewayEventAuthorizer] = None
    stage: str
    protocol: str
    identity: APIGatewayEventIdentity
    requestId: str
    requestTime: str
    requestTimeEpoch: datetime
    resourceId: Optional[str] = None
    resourcePath: str
    domainName: Optional[str] = None
    domainPrefix: Optional[str] = None
    extendedRequestId: Optional[str] = None
    httpMethod: Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    path: str
    connectedAt: Optional[datetime] = None
    connectionId: Optional[str] = None
    eventType: Optional[Literal["CONNECT", "MESSAGE", "DISCONNECT"]] = None
    messageDirection: Optional[str] = None
    messageId: Optional[str] = None
    routeKey: Optional[str] = None
    operationName: Optional[str] = None

    @root_validator(allow_reuse=True, skip_on_failure=True)
    def check_message_id(cls, values):
        message_id, event_type = values.get("messageId"), values.get("eventType")
        if message_id is not None and event_type != "MESSAGE":
            raise ValueError("messageId is available only when the `eventType` is `MESSAGE`")
        return values


class APIGatewayProxyEventModel(BaseModel):
    version: Optional[str] = None
    resource: str
    path: str
    httpMethod: Literal["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    headers: Dict[str, str]
    multiValueHeaders: Dict[str, List[str]]
    queryStringParameters: Optional[Dict[str, str]] = None
    multiValueQueryStringParameters: Optional[Dict[str, List[str]]] = None
    requestContext: APIGatewayEventRequestContext
    pathParameters: Optional[Dict[str, str]] = None
    stageVariables: Optional[Dict[str, str]] = None
    isBase64Encoded: Optional[bool] = None
    body: Optional[Union[str, Type[BaseModel]]] = None


class ApiGatewayAuthorizerToken(BaseModel):
    type: Literal["TOKEN"]
    methodArn: str
    authorizationToken: str


class ApiGatewayAuthorizerRequest(APIGatewayProxyEventModel):
    type: Literal["REQUEST"]
    methodArn: str
