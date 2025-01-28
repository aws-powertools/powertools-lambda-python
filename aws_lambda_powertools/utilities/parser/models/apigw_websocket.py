from datetime import datetime
from typing import Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyNetwork


class APIGatewayWebSocketEventIdentity(BaseModel):
    source_ip: IPvAnyNetwork = Field(alias="sourceIp")
    user_agent: Optional[str] = Field(None, alias="userAgent")


class APIGatewayWebSocketEventRequestContextBase(BaseModel):
    extended_request_id: str = Field(alias="extendedRequestId")
    request_time: str = Field(alias="requestTime")
    stage: str = Field(alias="stage")
    connected_at: datetime = Field(alias="connectedAt")
    request_time_epoch: datetime = Field(alias="requestTimeEpoch")
    identity: APIGatewayWebSocketEventIdentity = Field(alias="identity")
    request_id: str = Field(alias="requestId")
    domain_name: str = Field(alias="domainName")
    connection_id: str = Field(alias="connectionId")
    api_id: str = Field(alias="apiId")


class APIGatewayWebSocketMessageEventRequestContext(APIGatewayWebSocketEventRequestContextBase):
    route_key: str = Field(alias="routeKey")
    message_id: str = Field(alias="messageId")
    event_type: Literal["MESSAGE"] = Field(alias="eventType")
    message_direction: Literal["IN", "OUT"] = Field(alias="messageDirection")


class APIGatewayWebSocketConnectEventRequestContext(APIGatewayWebSocketEventRequestContextBase):
    route_key: Literal["$connect"] = Field(alias="routeKey")
    event_type: Literal["CONNECT"] = Field(alias="eventType")
    message_direction: Literal["IN"] = Field(alias="messageDirection")


class APIGatewayWebSocketDisconnectEventRequestContext(APIGatewayWebSocketEventRequestContextBase):
    route_key: Literal["$disconnect"] = Field(alias="routeKey")
    disconnect_status_code: int = Field(alias="disconnectStatusCode")
    event_type: Literal["DISCONNECT"] = Field(alias="eventType")
    message_direction: Literal["IN"] = Field(alias="messageDirection")
    disconnect_reason: str = Field(alias="disconnectReason")


class APIGatewayWebSocketConnectEventModel(BaseModel):
    headers: Dict[str, str] = Field(alias="headers")
    multi_value_headers: Dict[str, List[str]] = Field(alias="multiValueHeaders")
    request_context: APIGatewayWebSocketConnectEventRequestContext = Field(alias="requestContext")
    is_base64_encoded: bool = Field(alias="isBase64Encoded")


class APIGatewayWebSocketDisconnectEventModel(BaseModel):
    headers: Dict[str, str] = Field(alias="headers")
    multi_value_headers: Dict[str, List[str]] = Field(alias="multiValueHeaders")
    request_context: APIGatewayWebSocketDisconnectEventRequestContext = Field(alias="requestContext")
    is_base64_encoded: bool = Field(alias="isBase64Encoded")


class APIGatewayWebSocketMessageEventModel(BaseModel):
    request_context: APIGatewayWebSocketMessageEventRequestContext = Field(alias="requestContext")
    is_base64_encoded: bool = Field(alias="isBase64Encoded")
    body: Optional[Union[str, Type[BaseModel]]] = Field(None, alias="body")
