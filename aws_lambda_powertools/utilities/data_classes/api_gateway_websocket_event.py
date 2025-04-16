from __future__ import annotations

import base64
from functools import cached_property
from typing import Any

from aws_lambda_powertools.utilities.data_classes.common import (
    CaseInsensitiveDict,
    DictWrapper,
)


class APIGatewayWebSocketEventIdentity(DictWrapper):
    @property
    def source_ip(self) -> str:
        return self["sourceIp"]

    @property
    def user_agent(self) -> str | None:
        return self.get("userAgent")


class APIGatewayWebSocketEventRequestContext(DictWrapper):
    @property
    def route_key(self) -> str:
        return self["routeKey"]

    @property
    def disconnect_status_code(self) -> int | None:
        return self.get("disconnectStatusCode")

    @property
    def message_id(self) -> str | None:
        return self.get("messageId")

    @property
    def event_type(self) -> str:
        return self["eventType"]

    @property
    def extended_request_id(self) -> str:
        return self["extendedRequestId"]

    @property
    def request_time(self) -> str:
        return self["requestTime"]

    @property
    def message_direction(self) -> str:
        return self["messageDirection"]

    @property
    def disconnect_reason(self) -> str | None:
        return self.get("disconnectReason")

    @property
    def stage(self) -> str:
        return self["stage"]

    @property
    def connected_at(self) -> int:
        return self["connectedAt"]

    @property
    def request_time_epoch(self) -> int:
        return self["requestTimeEpoch"]

    @property
    def identity(self) -> APIGatewayWebSocketEventIdentity:
        return APIGatewayWebSocketEventIdentity(self["identity"])

    @property
    def request_id(self) -> str:
        return self["requestId"]

    @property
    def domain_name(self) -> str:
        return self["domainName"]

    @property
    def connection_id(self) -> str:
        return self["connectionId"]

    @property
    def api_id(self) -> str:
        return self["apiId"]


class APIGatewayWebSocketEvent(DictWrapper):
    """AWS proxy integration event for WebSocket API

    Documentation:
    --------------
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-integration-requests.html
    """

    @property
    def is_base64_encoded(self) -> bool:
        return self["isBase64Encoded"]

    @property
    def body(self) -> str | None:
        return self.get("body")

    @cached_property
    def decoded_body(self) -> str | None:
        body = self.body
        if self.is_base64_encoded and body:
            return base64.b64decode(body.encode()).decode()
        return body

    @cached_property
    def json_body(self) -> Any:
        if self.decoded_body:
            return self._json_deserializer(self.decoded_body)
        return None

    @property
    def headers(self) -> dict[str, str]:
        return CaseInsensitiveDict(self.get("headers"))

    @property
    def multi_value_headers(self) -> dict[str, list[str]]:
        return CaseInsensitiveDict(self.get("multiValueHeaders"))

    @property
    def query_string_parameters(self) -> dict[str, str]:
        return CaseInsensitiveDict(self.get("queryStringParameters"))

    @property
    def multi_value_query_string_parameters(self) -> dict[str, list[str]]:
        return CaseInsensitiveDict(self.get("multiValueQueryStringParameters"))

    @property
    def request_context(self) -> APIGatewayWebSocketEventRequestContext:
        return APIGatewayWebSocketEventRequestContext(self["requestContext"])
