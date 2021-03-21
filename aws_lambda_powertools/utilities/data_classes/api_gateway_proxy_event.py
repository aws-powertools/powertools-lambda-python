from typing import Any, Dict, List, Optional

from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent, DictWrapper


class APIGatewayEventIdentity(DictWrapper):
    @property
    def access_key(self) -> Optional[str]:
        return self["requestContext"]["identity"].get("accessKey")

    @property
    def account_id(self) -> Optional[str]:
        """The AWS account ID associated with the request."""
        return self["requestContext"]["identity"].get("accountId")

    @property
    def api_key(self) -> Optional[str]:
        """For API methods that require an API key, this variable is the API key associated with the method request.
        For methods that don't require an API key, this variable is null."""
        return self["requestContext"]["identity"].get("apiKey")

    @property
    def api_key_id(self) -> Optional[str]:
        """The API key ID associated with an API request that requires an API key."""
        return self["requestContext"]["identity"].get("apiKeyId")

    @property
    def caller(self) -> Optional[str]:
        """The principal identifier of the caller making the request."""
        return self["requestContext"]["identity"].get("caller")

    @property
    def cognito_authentication_provider(self) -> Optional[str]:
        """A comma-separated list of the Amazon Cognito authentication providers used by the caller
        making the request. Available only if the request was signed with Amazon Cognito credentials."""
        return self["requestContext"]["identity"].get("cognitoAuthenticationProvider")

    @property
    def cognito_authentication_type(self) -> Optional[str]:
        """The Amazon Cognito authentication type of the caller making the request.
        Available only if the request was signed with Amazon Cognito credentials."""
        return self["requestContext"]["identity"].get("cognitoAuthenticationType")

    @property
    def cognito_identity_id(self) -> Optional[str]:
        """The Amazon Cognito identity ID of the caller making the request.
        Available only if the request was signed with Amazon Cognito credentials."""
        return self["requestContext"]["identity"].get("cognitoIdentityId")

    @property
    def cognito_identity_pool_id(self) -> Optional[str]:
        """The Amazon Cognito identity pool ID of the caller making the request.
        Available only if the request was signed with Amazon Cognito credentials."""
        return self["requestContext"]["identity"].get("cognitoIdentityPoolId")

    @property
    def principal_org_id(self) -> Optional[str]:
        """The AWS organization ID."""
        return self["requestContext"]["identity"].get("principalOrgId")

    @property
    def source_ip(self) -> str:
        """The source IP address of the TCP connection making the request to API Gateway."""
        return self["requestContext"]["identity"]["sourceIp"]

    @property
    def user(self) -> Optional[str]:
        """The principal identifier of the user making the request."""
        return self["requestContext"]["identity"].get("user")

    @property
    def user_agent(self) -> Optional[str]:
        """The User Agent of the API caller."""
        return self["requestContext"]["identity"].get("userAgent")

    @property
    def user_arn(self) -> Optional[str]:
        """The Amazon Resource Name (ARN) of the effective user identified after authentication."""
        return self["requestContext"]["identity"].get("userArn")


class APIGatewayEventAuthorizer(DictWrapper):
    @property
    def claims(self) -> Optional[Dict[str, Any]]:
        return self["requestContext"]["authorizer"].get("claims")

    @property
    def scopes(self) -> Optional[List[str]]:
        return self["requestContext"]["authorizer"].get("scopes")


class APIGatewayEventRequestContext(DictWrapper):
    @property
    def account_id(self) -> str:
        """The AWS account ID associated with the request."""
        return self["requestContext"]["accountId"]

    @property
    def api_id(self) -> str:
        """The identifier API Gateway assigns to your API."""
        return self["requestContext"]["apiId"]

    @property
    def authorizer(self) -> APIGatewayEventAuthorizer:
        return APIGatewayEventAuthorizer(self._data)

    @property
    def connected_at(self) -> Optional[int]:
        """The Epoch-formatted connection time. (WebSocket API)"""
        return self["requestContext"].get("connectedAt")

    @property
    def connection_id(self) -> Optional[str]:
        """A unique ID for the connection that can be used to make a callback to the client. (WebSocket API)"""
        return self["requestContext"].get("connectionId")

    @property
    def domain_name(self) -> Optional[str]:
        """A domain name"""
        return self["requestContext"].get("domainName")

    @property
    def domain_prefix(self) -> Optional[str]:
        return self["requestContext"].get("domainPrefix")

    @property
    def event_type(self) -> Optional[str]:
        """The event type: `CONNECT`, `MESSAGE`, or `DISCONNECT`. (WebSocket API)"""
        return self["requestContext"].get("eventType")

    @property
    def extended_request_id(self) -> Optional[str]:
        """An automatically generated ID for the API call, which contains more useful information
        for debugging/troubleshooting."""
        return self["requestContext"].get("extendedRequestId")

    @property
    def protocol(self) -> str:
        """The request protocol, for example, HTTP/1.1."""
        return self["requestContext"]["protocol"]

    @property
    def http_method(self) -> str:
        """The HTTP method used. Valid values include: DELETE, GET, HEAD, OPTIONS, PATCH, POST, and PUT."""
        return self["requestContext"]["httpMethod"]

    @property
    def identity(self) -> APIGatewayEventIdentity:
        return APIGatewayEventIdentity(self._data)

    @property
    def message_direction(self) -> Optional[str]:
        """Message direction (WebSocket API)"""
        return self["requestContext"].get("messageDirection")

    @property
    def message_id(self) -> Optional[str]:
        """A unique server-side ID for a message. Available only when the `eventType` is `MESSAGE`."""
        return self["requestContext"].get("messageId")

    @property
    def path(self) -> str:
        return self["requestContext"]["path"]

    @property
    def stage(self) -> str:
        """The deployment stage of the API request """
        return self["requestContext"]["stage"]

    @property
    def request_id(self) -> str:
        """The ID that API Gateway assigns to the API request."""
        return self["requestContext"]["requestId"]

    @property
    def request_time(self) -> Optional[str]:
        """The CLF-formatted request time (dd/MMM/yyyy:HH:mm:ss +-hhmm)"""
        return self["requestContext"].get("requestTime")

    @property
    def request_time_epoch(self) -> int:
        """The Epoch-formatted request time."""
        return self["requestContext"]["requestTimeEpoch"]

    @property
    def resource_id(self) -> str:
        return self["requestContext"]["resourceId"]

    @property
    def resource_path(self) -> str:
        return self["requestContext"]["resourcePath"]

    @property
    def route_key(self) -> Optional[str]:
        """The selected route key."""
        return self["requestContext"].get("routeKey")


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
    def path(self) -> str:
        return self["path"]

    @property
    def http_method(self) -> str:
        """The HTTP method used. Valid values include: DELETE, GET, HEAD, OPTIONS, PATCH, POST, and PUT."""
        return self["httpMethod"]

    @property
    def multi_value_headers(self) -> Dict[str, List[str]]:
        return self["multiValueHeaders"]

    @property
    def multi_value_query_string_parameters(self) -> Optional[Dict[str, List[str]]]:
        return self.get("multiValueQueryStringParameters")

    @property
    def request_context(self) -> APIGatewayEventRequestContext:
        return APIGatewayEventRequestContext(self._data)

    @property
    def path_parameters(self) -> Optional[Dict[str, str]]:
        return self.get("pathParameters")

    @property
    def stage_variables(self) -> Optional[Dict[str, str]]:
        return self.get("stageVariables")


class RequestContextV2Http(DictWrapper):
    @property
    def method(self) -> str:
        return self["requestContext"]["http"]["method"]

    @property
    def path(self) -> str:
        return self["requestContext"]["http"]["path"]

    @property
    def protocol(self) -> str:
        """The request protocol, for example, HTTP/1.1."""
        return self["requestContext"]["http"]["protocol"]

    @property
    def source_ip(self) -> str:
        """The source IP address of the TCP connection making the request to API Gateway."""
        return self["requestContext"]["http"]["sourceIp"]

    @property
    def user_agent(self) -> str:
        """The User Agent of the API caller."""
        return self["requestContext"]["http"]["userAgent"]


class RequestContextV2AuthorizerIam(DictWrapper):
    @property
    def access_key(self) -> Optional[str]:
        """The IAM user access key associated with the request."""
        return self.get("accessKey")

    @property
    def account_id(self) -> Optional[str]:
        """The AWS account ID associated with the request."""
        return self.get("accountId")

    @property
    def caller_id(self) -> Optional[str]:
        """The principal identifier of the caller making the request."""
        return self.get("callerId")

    @property
    def cognito_amr(self) -> Optional[List[str]]:
        """This represents how the user was authenticated.
        AMR stands for  Authentication Methods References as per the openid spec"""
        return self["cognitoIdentity"].get("amr")

    @property
    def cognito_identity_id(self) -> Optional[str]:
        """The Amazon Cognito identity ID of the caller making the request.
        Available only if the request was signed with Amazon Cognito credentials."""
        return self["cognitoIdentity"].get("identityId")

    @property
    def cognito_identity_pool_id(self) -> Optional[str]:
        """The Amazon Cognito identity pool ID of the caller making the request.
        Available only if the request was signed with Amazon Cognito credentials."""
        return self["cognitoIdentity"].get("identityPoolId")

    @property
    def principal_org_id(self) -> Optional[str]:
        """The AWS organization ID."""
        return self.get("principalOrgId")

    @property
    def user_arn(self) -> Optional[str]:
        """The Amazon Resource Name (ARN) of the effective user identified after authentication."""
        return self.get("userArn")

    @property
    def user_id(self) -> Optional[str]:
        """The IAM user ID of the effective user identified after authentication."""
        return self.get("userId")


class RequestContextV2Authorizer(DictWrapper):
    @property
    def jwt_claim(self) -> Dict[str, Any]:
        return self["jwt"]["claims"]

    @property
    def jwt_scopes(self) -> List[str]:
        return self["jwt"]["scopes"]

    @property
    def get_lambda(self) -> Optional[Dict[str, Any]]:
        """Lambda authorization context details"""
        return self.get("lambda")

    @property
    def iam(self) -> Optional[RequestContextV2AuthorizerIam]:
        """IAM authorization details used for making the request."""
        iam = self.get("iam")
        return None if iam is None else RequestContextV2AuthorizerIam(iam)


class RequestContextV2(DictWrapper):
    @property
    def account_id(self) -> str:
        """The AWS account ID associated with the request."""
        return self["requestContext"]["accountId"]

    @property
    def api_id(self) -> str:
        """The identifier API Gateway assigns to your API."""
        return self["requestContext"]["apiId"]

    @property
    def authorizer(self) -> Optional[RequestContextV2Authorizer]:
        authorizer = self["requestContext"].get("authorizer")
        return None if authorizer is None else RequestContextV2Authorizer(authorizer)

    @property
    def domain_name(self) -> str:
        """A domain name """
        return self["requestContext"]["domainName"]

    @property
    def domain_prefix(self) -> str:
        return self["requestContext"]["domainPrefix"]

    @property
    def http(self) -> RequestContextV2Http:
        return RequestContextV2Http(self._data)

    @property
    def request_id(self) -> str:
        """The ID that API Gateway assigns to the API request."""
        return self["requestContext"]["requestId"]

    @property
    def route_key(self) -> str:
        """The selected route key."""
        return self["requestContext"]["routeKey"]

    @property
    def stage(self) -> str:
        """The deployment stage of the API request """
        return self["requestContext"]["stage"]

    @property
    def time(self) -> str:
        """The CLF-formatted request time (dd/MMM/yyyy:HH:mm:ss +-hhmm)."""
        return self["requestContext"]["time"]

    @property
    def time_epoch(self) -> int:
        """The Epoch-formatted request time."""
        return self["requestContext"]["timeEpoch"]


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
