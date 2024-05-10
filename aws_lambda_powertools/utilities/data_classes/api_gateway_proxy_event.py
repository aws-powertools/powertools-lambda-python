from typing import Any, Dict, List, Optional

from aws_lambda_powertools.shared.headers_serializer import (
    BaseHeadersSerializer,
    HttpApiHeadersSerializer,
    MultiValueHeadersSerializer,
)
from aws_lambda_powertools.utilities.data_classes.common import (
    BaseProxyEvent,
    BaseRequestContext,
    BaseRequestContextV2,
    DictWrapper,
)


class APIGatewayEventAuthorizer(DictWrapper):
    @property
    def claims(self) -> Dict[str, Any]:
        return self.get("claims") or {}  # key might exist but can be `null`

    @property
    def scopes(self) -> List[str]:
        return self.get("scopes") or []  # key might exist but can be `null`

    @property
    def principal_id(self) -> str:
        """The principal user identification associated with the token sent by the client and returned from an
        API Gateway Lambda authorizer (formerly known as a custom authorizer)"""
        return self.get("principalId") or ""  # key might exist but can be `null`

    @property
    def integration_latency(self) -> Optional[int]:
        """The authorizer latency in ms."""
        return self.get("integrationLatency")

    def get_context(self) -> Dict[str, Any]:
        """Retrieve the authorization context details injected by a Lambda Authorizer.

        Example
        --------

        ```python
        ctx: dict = request_context.authorizer.get_context()

        tenant_id = ctx.get("tenant_id")
        ```

        Returns:
        --------
        Dict[str, Any]
            A dictionary containing Lambda authorization context details.
        """
        return self._data


class APIGatewayEventRequestContext(BaseRequestContext):
    @property
    def connected_at(self) -> Optional[int]:
        """The Epoch-formatted connection time. (WebSocket API)"""
        return self["requestContext"].get("connectedAt")

    @property
    def connection_id(self) -> Optional[str]:
        """A unique ID for the connection that can be used to make a callback to the client. (WebSocket API)"""
        return self["requestContext"].get("connectionId")

    @property
    def event_type(self) -> Optional[str]:
        """The event type: `CONNECT`, `MESSAGE`, or `DISCONNECT`. (WebSocket API)"""
        return self["requestContext"].get("eventType")

    @property
    def message_direction(self) -> Optional[str]:
        """Message direction (WebSocket API)"""
        return self["requestContext"].get("messageDirection")

    @property
    def message_id(self) -> Optional[str]:
        """A unique server-side ID for a message. Available only when the `eventType` is `MESSAGE`."""
        return self["requestContext"].get("messageId")

    @property
    def operation_name(self) -> Optional[str]:
        """The name of the operation being performed"""
        return self["requestContext"].get("operationName")

    @property
    def route_key(self) -> Optional[str]:
        """The selected route key."""
        return self["requestContext"].get("routeKey")

    @property
    def authorizer(self) -> APIGatewayEventAuthorizer:
        authz_data = self._data.get("requestContext", {}).get("authorizer", {})
        return APIGatewayEventAuthorizer(authz_data)


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
    def multi_value_headers(self) -> Dict[str, List[str]]:
        return self.get("multiValueHeaders") or {}  # key might exist but can be `null`

    @property
    def multi_value_query_string_parameters(self) -> Dict[str, List[str]]:
        return self.get("multiValueQueryStringParameters") or {}  # key might exist but can be `null`

    @property
    def resolved_query_string_parameters(self) -> Dict[str, List[str]]:
        if self.multi_value_query_string_parameters:
            return self.multi_value_query_string_parameters

        return super().resolved_query_string_parameters

    @property
    def resolved_headers_field(self) -> Dict[str, Any]:
        headers: Dict[str, Any] = {}

        if self.multi_value_headers:
            headers = self.multi_value_headers
        else:
            headers = self.headers

        return {key.lower(): value for key, value in headers.items()}

    @property
    def request_context(self) -> APIGatewayEventRequestContext:
        return APIGatewayEventRequestContext(self._data)

    @property
    def path_parameters(self) -> Optional[Dict[str, str]]:
        return self.get("pathParameters")

    @property
    def stage_variables(self) -> Optional[Dict[str, str]]:
        return self.get("stageVariables")

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

    def _cognito_identity(self) -> Dict:
        return self.get("cognitoIdentity") or {}  # not available in FunctionURL; key might exist but can be `null`

    @property
    def cognito_amr(self) -> List[str]:
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
    def jwt_claim(self) -> Dict[str, Any]:
        jwt = self.get("jwt") or {}  # not available in FunctionURL; key might exist but can be `null`
        return jwt.get("claims") or {}  # key might exist but can be `null`

    @property
    def jwt_scopes(self) -> List[str]:
        jwt = self.get("jwt") or {}  # not available in FunctionURL; key might exist but can be `null`
        return jwt.get("scopes", [])

    @property
    def get_lambda(self) -> Dict[str, Any]:
        """Lambda authorization context details"""
        return self.get("lambda") or {}  # key might exist but can be `null`

    def get_context(self) -> Dict[str, Any]:
        """Retrieve the authorization context details injected by a Lambda Authorizer.

        Example
        --------

        ```python
        ctx: dict = request_context.authorizer.get_context()

        tenant_id = ctx.get("tenant_id")
        ```

        Returns:
        --------
        Dict[str, Any]
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
        ctx = self.get("requestContext") or {}  # key might exist but can be `null`
        return RequestContextV2Authorizer(ctx.get("authorizer", {}))


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
    def cookies(self) -> Optional[List[str]]:
        return self.get("cookies")

    @property
    def request_context(self) -> RequestContextV2:
        return RequestContextV2(self._data)

    @property
    def path_parameters(self) -> Optional[Dict[str, str]]:
        return self.get("pathParameters")

    @property
    def stage_variables(self) -> Optional[Dict[str, str]]:
        return self.get("stageVariables")

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

    @property
    def resolved_headers_field(self) -> Dict[str, Any]:
        if self.headers is not None:
            headers = {key.lower(): value.split(",") if "," in value else value for key, value in self.headers.items()}
            return headers

        return {}
