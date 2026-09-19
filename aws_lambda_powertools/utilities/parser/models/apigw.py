from datetime import datetime
from typing import Any, Dict, List, Literal, Type, Union

from pydantic import BaseModel, field_validator, model_validator
from pydantic.networks import IPvAnyNetwork

from aws_lambda_powertools.utilities.parser.functions import _validate_source_ip


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
    sourceIp: Union[IPvAnyNetwork, str]
    user: str | None = None
    userAgent: str | None = None
    userArn: str | None = None
    clientCert: ApiGatewayUserCert | None = None

    @field_validator("sourceIp", mode="before")
    @classmethod
    def _validate_source_ip(cls, value):
        return _validate_source_ip(value=value)


class APIGatewayEventAuthorizer(BaseModel):
    claims: Dict[str, Any] | None = None
    scopes: List[str] | None = None


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
    headers: Dict[str, str]
    multiValueHeaders: Dict[str, List[str]]
    queryStringParameters: Dict[str, str] | None = None
    multiValueQueryStringParameters: Dict[str, List[str]] | None = None
    requestContext: APIGatewayEventRequestContext
    pathParameters: Dict[str, str] | None = None
    stageVariables: Dict[str, str] | None = None
    isBase64Encoded: bool | None = None
    body: Union[str, Type[BaseModel]] | None = None


class ApiGatewayAuthorizerToken(BaseModel):
    type: Literal["TOKEN"]
    methodArn: str
    authorizationToken: str


class ApiGatewayAuthorizerRequest(APIGatewayProxyEventModel):
    type: Literal["REQUEST"]
    methodArn: str
