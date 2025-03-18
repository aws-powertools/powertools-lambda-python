from __future__ import annotations

from functools import cached_property
from typing import Any

from aws_lambda_powertools.shared.headers_serializer import (
    BaseHeadersSerializer,
    HttpApiHeadersSerializer,
    MultiValueHeadersSerializer,
)
from aws_lambda_powertools.utilities.data_classes.common import (
    BaseProxyEvent,
    BaseRequestContext,
    BaseRequestContextV2,
    CaseInsensitiveDict,
    DictWrapper,
)


class APIGatewayEventAuthorizer(DictWrapper):
    @property
    def claims(self) -> dict[str, Any]:
        return self.get("claims") or {}  # key might exist but can be `null`

    @property
    def scopes(self) -> list[str]:
        return self.get("scopes") or []  # key might exist but can be `null`

    @property
    def principal_id(self) -> str:
        """The principal user identification associated with the token sent by the client and returned from an
        API Gateway Lambda authorizer (formerly known as a custom authorizer)"""
        return self.get("principalId") or ""  # key might exist but can be `null`

    @property
    def integration_latency(self) -> int | None:
        """The authorizer latency in ms."""
        return self.get("integrationLatency")

    def get_context(self) -> dict[str, Any]:
        """Retrieve the authorization context details injected by a Lambda Authorizer.

        Example
        --------

        ```python
        ctx: dict = request_context.authorizer.get_context()

        tenant_id = ctx.get("tenant_id")
        ```

        Returns:
        --------
        dict[str, Any]
            A dictionary containing Lambda authorization context details.
        """
        return self._data


class APIGatewayEventRequestContext(BaseRequestContext):
    @property
    def connected_at(self) -> int | None:
        """The Epoch-formatted connection time. (WebSocket API)"""
        return self.get("connectedAt")

    @property
    def connection_id(self) -> str | None:
        """A unique ID for the connection that can be used to make a callback to the client. (WebSocket API)"""
        return self.get("connectionId")

    @property
    def event_type(self) -> str | None:
        """The event type: `CONNECT`, `MESSAGE`, or `DISCONNECT`. (WebSocket API)"""
        return self.get("eventType")

    @property
    def message_direction(self) -> str | None:
        """Message direction (WebSocket API)"""
        return self.get("messageDirection")

    @property
    def message_id(self) -> str | None:
        """A unique server-side ID for a message. Available only when the `eventType` is `MESSAGE`."""
        return self.get("messageId")

    @property
    def operation_name(self) -> str | None:
        """The name of the operation being performed"""
        return self.get("operationName")

    @property
    def route_key(self) -> str | None:
        """The selected route key."""
        return self.get("routeKey")

    @property
    def authorizer(self) -> APIGatewayEventAuthorizer:
        return APIGatewayEventAuthorizer(self.get("authorizer") or {})


class APIGatewayProxyEvent(BaseProxyEvent):
    """AWS Lambda proxy V1

    Documentation:
    --------------
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
    """

    @property
    def version(self) -> str:
        return self["version"]

    @property
    def resource(self) -> str:
        return self["resource"]

    @property
    def multi_value_headers(self) -> dict[str, list[str]]:
        return CaseInsensitiveDict(self.get("multiValueHeaders"))

    @property
    def resolved_query_string_parameters(self) -> dict[str, list[str]]:
        return self.multi_value_query_string_parameters or super().resolved_query_string_parameters

    @property
    def resolved_headers_field(self) -> dict[str, Any]:
        return self.multi_value_headers or self.headers

    @property
    def request_context(self) -> APIGatewayEventRequestContext:
        return APIGatewayEventRequestContext(self["requestContext"])

    @property
    def path_parameters(self) -> dict[str, str]:
        return self.get("pathParameters") or {}

    @property
    def stage_variables(self) -> dict[str, str]:
        return self.get("stageVariables") or {}

    def header_serializer(self) -> BaseHeadersSerializer:
        return MultiValueHeadersSerializer()


class RequestContextV2AuthorizerIam(DictWrapper):
    @property
    def access_key(self) -> str:
        """The IAM user access key associated with the request."""
        return self.get("accessKey") or ""  # key might exist but can be `null`

    @property
    def account_id(self) -> str:
        """The AWS account ID associated with the request."""
        return self.get("accountId") or ""  # key might exist but can be `null`

    @property
    def caller_id(self) -> str:
        """The principal identifier of the caller making the request."""
        return self.get("callerId") or ""  # key might exist but can be `null`

    def _cognito_identity(self) -> dict:
        return self.get("cognitoIdentity") or {}  # not available in FunctionURL; key might exist but can be `null`

    @property
    def cognito_amr(self) -> list[str]:
        """This represents how the user was authenticated.
        AMR stands for  Authentication Methods References as per the openid spec"""
        return self._cognito_identity().get("amr", [])

    @property
    def cognito_identity_id(self) -> str:
        """The Amazon Cognito identity ID of the caller making the request.
        Available only if the request was signed with Amazon Cognito credentials."""
        return self._cognito_identity().get("identityId", "")

    @property
    def cognito_identity_pool_id(self) -> str:
        """The Amazon Cognito identity pool ID of the caller making the request.
        Available only if the request was signed with Amazon Cognito credentials."""
        return self._cognito_identity().get("identityPoolId") or ""  # key might exist but can be `null`

    @property
    def principal_org_id(self) -> str:
        """The AWS organization ID."""
        return self.get("principalOrgId") or ""  # key might exist but can be `null`

    @property
    def user_arn(self) -> str:
        """The Amazon Resource Name (ARN) of the effective user identified after authentication."""
        return self.get("userArn") or ""  # key might exist but can be `null`

    @property
    def user_id(self) -> str:
        """The IAM user ID of the effective user identified after authentication."""
        return self.get("userId") or ""  # key might exist but can be `null`


class RequestContextV2Authorizer(DictWrapper):
    @property
    def jwt_claim(self) -> dict[str, Any]:
        jwt = self.get("jwt") or {}  # not available in FunctionURL; key might exist but can be `null`
        return jwt.get("claims") or {}  # key might exist but can be `null`

    @property
    def jwt_scopes(self) -> list[str]:
        jwt = self.get("jwt") or {}  # not available in FunctionURL; key might exist but can be `null`
        return jwt.get("scopes", [])

    @property
    def get_lambda(self) -> dict[str, Any]:
        """Lambda authorization context details"""
        return self.get("lambda") or {}  # key might exist but can be `null`

    def get_context(self) -> dict[str, Any]:
        """Retrieve the authorization context details injected by a Lambda Authorizer.

        Example
        --------

        ```python
        ctx: dict = request_context.authorizer.get_context()

        tenant_id = ctx.get("tenant_id")
        ```

        Returns:
        --------
        dict[str, Any]
            A dictionary containing Lambda authorization context details.
        """
        return self.get_lambda

    @property
    def iam(self) -> RequestContextV2AuthorizerIam:
        """IAM authorization details used for making the request."""
        iam = self.get("iam") or {}  # key might exist but can be `null`
        return RequestContextV2AuthorizerIam(iam)


class RequestContextV2(BaseRequestContextV2):
    @property
    def authorizer(self) -> RequestContextV2Authorizer:
        return RequestContextV2Authorizer(self.get("authorizer") or {})


class APIGatewayProxyEventV2(BaseProxyEvent):
    """AWS Lambda proxy V2 event

    Notes:
    -----
    Format 2.0 doesn't have multiValueHeaders or multiValueQueryStringParameters fields. Duplicate headers
    are combined with commas and included in the headers field. Duplicate query strings are combined with
    commas and included in the queryStringParameters field.

    Format 2.0 includes a new cookies field. All cookie headers in the request are combined with commas and
    added to the cookies field. In the response to the client, each cookie becomes a set-cookie header.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
    """

    @property
    def version(self) -> str:
        return self["version"]

    @property
    def route_key(self) -> str:
        return self["routeKey"]

    @property
    def raw_path(self) -> str:
        return self["rawPath"]

    @property
    def raw_query_string(self) -> str:
        return self["rawQueryString"]

    @property
    def cookies(self) -> list[str]:
        return self.get("cookies") or []

    @property
    def request_context(self) -> RequestContextV2:
        return RequestContextV2(self["requestContext"])

    @property
    def path_parameters(self) -> dict[str, str]:
        return self.get("pathParameters") or {}

    @property
    def stage_variables(self) -> dict[str, str]:
        return self.get("stageVariables") or {}

    @property
    def path(self) -> str:
        stage = self.request_context.stage
        if stage != "$default":
            return self.raw_path[len("/" + stage) :]
        return self.raw_path

    @property
    def http_method(self) -> str:
        """The HTTP method used. Valid values include: DELETE, GET, HEAD, OPTIONS, PATCH, POST, and PUT."""
        return self.request_context.http.method

    def header_serializer(self):
        return HttpApiHeadersSerializer()

    @cached_property
    def resolved_headers_field(self) -> dict[str, Any]:
        return CaseInsensitiveDict((k, v.split(",") if "," in v else v) for k, v in self.headers.items())
