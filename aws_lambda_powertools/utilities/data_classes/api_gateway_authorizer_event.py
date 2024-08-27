from __future__ import annotations

import enum
import re
import warnings
from typing import Any, overload

from typing_extensions import deprecated

from aws_lambda_powertools.utilities.data_classes.common import (
    BaseRequestContext,
    BaseRequestContextV2,
    CaseInsensitiveDict,
    DictWrapper,
)
from aws_lambda_powertools.utilities.data_classes.shared_functions import (
    get_header_value,
)
from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning


class APIGatewayRouteArn:
    """A parsed route arn"""

    def __init__(
        self,
        region: str,
        aws_account_id: str,
        api_id: str,
        stage: str,
        http_method: str,
        resource: str,
        partition: str = "aws",
    ):
        self.partition = partition
        self.region = region
        self.aws_account_id = aws_account_id
        self.api_id = api_id
        self.stage = stage
        self.http_method = http_method
        # Remove matching "/" from `resource`.
        self.resource = resource.lstrip("/")

    @property
    def arn(self) -> str:
        """Build an arn from its parts
        eg: arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"""
        return (
            f"arn:{self.partition}:execute-api:{self.region}:{self.aws_account_id}:{self.api_id}/{self.stage}/"
            f"{self.http_method}/{self.resource}"
        )


def parse_api_gateway_arn(arn: str) -> APIGatewayRouteArn:
    """Parses a gateway route arn as a APIGatewayRouteArn class

    Parameters
    ----------
    arn : str
        ARN string for a methodArn or a routeArn
    Returns
    -------
    APIGatewayRouteArn
    """
    arn_parts = arn.split(":")
    api_gateway_arn_parts = arn_parts[5].split("/")
    return APIGatewayRouteArn(
        partition=arn_parts[1],
        region=arn_parts[3],
        aws_account_id=arn_parts[4],
        api_id=api_gateway_arn_parts[0],
        stage=api_gateway_arn_parts[1],
        http_method=api_gateway_arn_parts[2],
        # conditional allow us to handle /path/{proxy+} resources, as their length changes.
        resource="/".join(api_gateway_arn_parts[3:]) if len(api_gateway_arn_parts) >= 4 else "",
    )


class APIGatewayAuthorizerTokenEvent(DictWrapper):
    """API Gateway Authorizer Token Event Format 1.0

    Documentation:
    -------------
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
    """

    @property
    def get_type(self) -> str:
        return self["type"]

    @property
    def authorization_token(self) -> str:
        return self["authorizationToken"]

    @property
    def method_arn(self) -> str:
        """ARN of the incoming method request and is populated by API Gateway in accordance with the Lambda authorizer
        configuration"""
        return self["methodArn"]

    @property
    def parsed_arn(self) -> APIGatewayRouteArn:
        """Convenient property to return a parsed api gateway method arn"""
        return parse_api_gateway_arn(self.method_arn)


class APIGatewayAuthorizerRequestEvent(DictWrapper):
    """API Gateway Authorizer Request Event Format 1.0

    Documentation:
    -------------
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html
    """

    @property
    def version(self) -> str:
        return self["version"]

    @property
    def get_type(self) -> str:
        return self["type"]

    @property
    def method_arn(self) -> str:
        return self["methodArn"]

    @property
    def parsed_arn(self) -> APIGatewayRouteArn:
        return parse_api_gateway_arn(self.method_arn)

    @property
    def identity_source(self) -> str:
        return self["identitySource"]

    @property
    def authorization_token(self) -> str:
        return self["authorizationToken"]

    @property
    def resource(self) -> str:
        return self["resource"]

    @property
    def path(self) -> str:
        return self["path"]

    @property
    def http_method(self) -> str:
        return self["httpMethod"]

    @property
    def headers(self) -> dict[str, str]:
        return CaseInsensitiveDict(self["headers"])

    @property
    def query_string_parameters(self) -> dict[str, str]:
        return self["queryStringParameters"]

    @property
    def path_parameters(self) -> dict[str, str]:
        return self["pathParameters"]

    @property
    def stage_variables(self) -> dict[str, str]:
        return self["stageVariables"]

    @property
    def request_context(self) -> BaseRequestContext:
        return BaseRequestContext(self._data)

    @overload
    def get_header_value(
        self,
        name: str,
        default_value: str,
        case_sensitive: bool = False,
    ) -> str: ...

    @overload
    def get_header_value(
        self,
        name: str,
        default_value: str | None = None,
        case_sensitive: bool = False,
    ) -> str | None: ...

    @deprecated(
        "`get_header_value` function is deprecated; Access headers directly using event.headers.get('HeaderName')",
        category=None,
    )
    def get_header_value(
        self,
        name: str,
        default_value: str | None = None,
        case_sensitive: bool = False,
    ) -> str | None:
        """Get header value by name
        Parameters
        ----------
        name: str
            Header name
        default_value: str, optional
            Default value if no value was found by name
        case_sensitive: bool
            Whether to use a case-sensitive look up
        Returns
        -------
        str, optional
            Header value
        """
        warnings.warn(
            "The `get_header_value` function is deprecated in V3 and the `case_sensitive` parameter "
            "no longer has any effect. This function will be removed in the next major version. "
            "Instead, access headers directly using event.headers.get('HeaderName'), which is case insensitive.",
            category=PowertoolsDeprecationWarning,
            stacklevel=2,
        )
        return get_header_value(self.headers, name, default_value, case_sensitive)


class APIGatewayAuthorizerEventV2(DictWrapper):
    """API Gateway Authorizer Event Format 2.0

    Documentation:
    -------------
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html
    - https://aws.amazon.com/blogs/compute/introducing-iam-and-lambda-authorizers-for-amazon-api-gateway-http-apis/
    """

    @property
    def version(self) -> str:
        """Event payload version should always be 2.0"""
        return self["version"]

    @property
    def get_type(self) -> str:
        """Event type should always be request"""
        return self["type"]

    @property
    def route_arn(self) -> str:
        """ARN of the route being called

        eg: arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"""
        return self["routeArn"]

    @property
    def parsed_arn(self) -> APIGatewayRouteArn:
        """Convenient property to return a parsed api gateway route arn"""
        return parse_api_gateway_arn(self.route_arn)

    @property
    def identity_source(self) -> list[str]:
        """The identity source for which authorization is requested.

        For a REQUEST authorizer, this is optional. The value is a set of one or more mapping expressions of the
        specified request parameters. The identity source can be headers, query string parameters, stage variables,
        and context parameters.
        """
        return self.get("identitySource") or []

    @property
    def route_key(self) -> str:
        """The route key for the route. For HTTP APIs, the route key can be either $default,
        or a combination of an HTTP method and resource path, for example, GET /pets."""
        return self["routeKey"]

    @property
    def raw_path(self) -> str:
        return self["rawPath"]

    @property
    def raw_query_string(self) -> str:
        return self["rawQueryString"]

    @property
    def cookies(self) -> list[str]:
        """Cookies"""
        return self["cookies"]

    @property
    def headers(self) -> dict[str, str]:
        """Http headers"""
        return CaseInsensitiveDict(self["headers"])

    @property
    def query_string_parameters(self) -> dict[str, str]:
        return self["queryStringParameters"]

    @property
    def request_context(self) -> BaseRequestContextV2:
        return BaseRequestContextV2(self._data)

    @property
    def path_parameters(self) -> dict[str, str]:
        return self.get("pathParameters") or {}

    @property
    def stage_variables(self) -> dict[str, str]:
        return self.get("stageVariables") or {}

    @overload
    def get_header_value(self, name: str, default_value: str, case_sensitive: bool = False) -> str: ...

    @overload
    def get_header_value(
        self,
        name: str,
        default_value: str | None = None,
        case_sensitive: bool = False,
    ) -> str | None: ...

    @deprecated(
        "`get_header_value` function is deprecated; Access headers directly using event.headers.get('HeaderName')",
        category=None,
    )
    def get_header_value(
        self,
        name: str,
        default_value: str | None = None,
        case_sensitive: bool = False,
    ) -> str | None:
        """Get header value by name
        Parameters
        ----------
        name: str
            Header name
        default_value: str, optional
            Default value if no value was found by name
        case_sensitive: bool
            Whether to use a case-sensitive look up
        Returns
        -------
        str, optional
            Header value
        """
        warnings.warn(
            "The `get_header_value` function is deprecated in V3 and the `case_sensitive` parameter "
            "no longer has any effect. This function will be removed in the next major version. "
            "Instead, access headers directly using event.headers.get('HeaderName'), which is case insensitive.",
            category=PowertoolsDeprecationWarning,
            stacklevel=2,
        )
        return get_header_value(self.headers, name, default_value, case_sensitive)


class APIGatewayAuthorizerResponseV2:
    """Api Gateway HTTP API V2 payload authorizer simple response helper

    Parameters
    ----------
    authorize: bool
        authorize is a boolean value indicating if the value in authorizationToken
        is authorized to make calls to the GraphQL API. If this value is
        true, execution of the GraphQL API continues. If this value is false,
        an UnauthorizedException is raised
    context: dict[str, Any], optional
        A JSON object visible as `event.requestContext.authorizer` lambda event

        The context object only supports key-value pairs. Nested keys are not supported.

        Warning: The total size of this JSON object must not exceed 5MB.
    """

    def __init__(
        self,
        authorize: bool = False,
        context: dict[str, Any] | None = None,
    ):
        self.authorize = authorize
        self.context = context

    def asdict(self) -> dict:
        """Return the response as a dict"""
        response: dict = {"isAuthorized": self.authorize}

        if self.context:
            response["context"] = self.context

        return response


class HttpVerb(enum.Enum):
    """Enum of http methods / verbs"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    HEAD = "HEAD"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    ALL = "*"


DENY_ALL_RESPONSE = {
    "principalId": "deny-all-user",
    "policyDocument": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "execute-api:Invoke",
                "Effect": "Deny",
                "Resource": ["*"],
            },
        ],
    },
}


class APIGatewayAuthorizerResponse:
    """The IAM Policy Response required for API Gateway REST APIs and HTTP APIs.

    Based on: - https://github.com/awslabs/aws-apigateway-lambda-authorizer-blueprints/blob/\
    master/blueprints/python/api-gateway-authorizer-python.py

    Documentation:
    -------------
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-lambda-authorizer-output.html
    """

    path_regex = r"^[/.a-zA-Z0-9-_\*]+$"
    """The regular expression used to validate resource paths for the policy"""

    def __init__(
        self,
        principal_id: str,
        region: str,
        aws_account_id: str,
        api_id: str,
        stage: str,
        context: dict | None = None,
        usage_identifier_key: str | None = None,
        partition: str = "aws",
    ):
        """
        Parameters
        ----------
        principal_id : str
            The principal used for the policy, this should be a unique identifier for the end user
        region : str
            AWS Regions. Beware of using '*' since it will not simply mean any region, because stars will greedily
            expand over '/' or other separators.
            See https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_resource.html for more
            details.
        aws_account_id : str
            The AWS account id the policy will be generated for. This is used to create the method ARNs.
        api_id : str
            The API Gateway API id to be used in the policy.
            Beware of using '*' since it will not simply mean any API Gateway API id, because stars will greedily
            expand over '/' or other separators.
            See https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_resource.html for more
            details.
        stage : str
            The default stage to be used in the policy.
            Beware of using '*' since it will not simply mean any stage, because stars will
            greedily expand over '/' or other separators.
            See https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_resource.html for more
            details.
        context : dict, optional
            Optional, context.
            Note: only names of type string and values of type int, string or boolean are supported
        usage_identifier_key: str, optional
            If the API uses a usage plan (the apiKeySource is set to `AUTHORIZER`), the Lambda authorizer function
            must return one of the usage plan's API keys as the usageIdentifierKey property value.
            > **Note:** This only applies for REST APIs.
        partition: str, optional
            Optional, arn partition.
            See https://docs.aws.amazon.com/IAM/latest/UserGuide/reference-arns.html
        """
        self.principal_id = principal_id
        self.region = region
        self.aws_account_id = aws_account_id
        self.api_id = api_id
        self.stage = stage
        self.context = context
        self.usage_identifier_key = usage_identifier_key
        self._allow_routes: list[dict] = []
        self._deny_routes: list[dict] = []
        self._resource_pattern = re.compile(self.path_regex)
        self.partition = partition

    @staticmethod
    def from_route_arn(
        arn: str,
        principal_id: str,
        context: dict | None = None,
        usage_identifier_key: str | None = None,
    ) -> APIGatewayAuthorizerResponse:
        parsed_arn = parse_api_gateway_arn(arn)
        return APIGatewayAuthorizerResponse(
            principal_id,
            parsed_arn.region,
            parsed_arn.aws_account_id,
            parsed_arn.api_id,
            parsed_arn.stage,
            context,
            usage_identifier_key,
        )

    def _add_route(self, effect: str, http_method: str, resource: str, conditions: list[dict] | None = None):
        """Adds a route to the internal lists of allowed or denied routes. Each object in
        the internal list contains a resource ARN and a condition statement. The condition
        statement can be null."""
        if http_method != "*" and http_method not in HttpVerb.__members__:
            allowed_values = [verb.value for verb in HttpVerb]
            raise ValueError(f"Invalid HTTP verb: '{http_method}'. Use either '{allowed_values}'")

        if not self._resource_pattern.match(resource):
            raise ValueError(f"Invalid resource path: {resource}. Path should match {self.path_regex}")

        resource_arn = APIGatewayRouteArn(
            self.region,
            self.aws_account_id,
            self.api_id,
            self.stage,
            http_method,
            resource,
            self.partition,
        ).arn

        route = {"resourceArn": resource_arn, "conditions": conditions}

        if effect.lower() == "allow":
            self._allow_routes.append(route)
        else:  # deny
            self._deny_routes.append(route)

    @staticmethod
    def _get_empty_statement(effect: str) -> dict[str, Any]:
        """Returns an empty statement object prepopulated with the correct action and the desired effect."""
        return {"Action": "execute-api:Invoke", "Effect": effect.capitalize(), "Resource": []}

    def _get_statement_for_effect(self, effect: str, routes: list[dict]) -> list[dict]:
        """This function loops over an array of objects containing a `resourceArn` and
        `conditions` statement and generates the array of statements for the policy."""
        if not routes:
            return []

        statements: list[dict] = []
        statement = self._get_empty_statement(effect)

        for route in routes:
            resource_arn = route["resourceArn"]
            conditions = route.get("conditions")
            if conditions is not None and len(conditions) > 0:
                conditional_statement = self._get_empty_statement(effect)
                conditional_statement["Resource"].append(resource_arn)
                conditional_statement["Condition"] = conditions
                statements.append(conditional_statement)

            else:
                statement["Resource"].append(resource_arn)

        if len(statement["Resource"]) > 0:
            statements.append(statement)

        return statements

    def allow_all_routes(self, http_method: str = HttpVerb.ALL.value):
        """Adds a '*' allow to the policy to authorize access to all methods of an API

        Parameters
        ----------
        http_method: str
        """
        self._add_route(effect="Allow", http_method=http_method, resource="*")

    def deny_all_routes(self, http_method: str = HttpVerb.ALL.value):
        """Adds a '*' allow to the policy to deny access to all methods of an API

        Parameters
        ----------
        http_method: str
        """

        self._add_route(effect="Deny", http_method=http_method, resource="*")

    def allow_route(self, http_method: str, resource: str, conditions: list[dict] | None = None):
        """Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods for the policy.

        Optionally includes a condition for the policy statement. More on AWS policy
        conditions here: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition"""
        self._add_route(effect="Allow", http_method=http_method, resource=resource, conditions=conditions)

    def deny_route(self, http_method: str, resource: str, conditions: list[dict] | None = None):
        """Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods for the policy.

        Optionally includes a condition for the policy statement. More on AWS policy
        conditions here: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition"""
        self._add_route(effect="Deny", http_method=http_method, resource=resource, conditions=conditions)

    def asdict(self) -> dict[str, Any]:
        """Generates the policy document based on the internal lists of allowed and denied
        conditions. This will generate a policy with two main statements for the effect:
        one statement for Allow and one statement for Deny.
        Methods that includes conditions will have their own statement in the policy."""
        if len(self._allow_routes) == 0 and len(self._deny_routes) == 0:
            raise ValueError("No statements defined for the policy")

        response: dict[str, Any] = {
            "principalId": self.principal_id,
            "policyDocument": {"Version": "2012-10-17", "Statement": []},
        }

        response["policyDocument"]["Statement"].extend(self._get_statement_for_effect("Allow", self._allow_routes))
        response["policyDocument"]["Statement"].extend(self._get_statement_for_effect("Deny", self._deny_routes))

        if self.usage_identifier_key:
            response["usageIdentifierKey"] = self.usage_identifier_key

        if self.context:
            response["context"] = self.context

        return response
