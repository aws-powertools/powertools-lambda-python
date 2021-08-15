from typing import Dict, List, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class AppSyncAuthorizerEventRequestContext(DictWrapper):
    """Request context"""

    @property
    def api_id(self) -> str:
        """AppSync api id"""
        return self["requestContext"]["apiId"]

    @property
    def account_id(self) -> str:
        """AWS Account ID"""
        return self["requestContext"]["accountId"]

    @property
    def request_id(self) -> str:
        """Requestt ID"""
        return self["requestContext"]["requestId"]

    @property
    def query_string(self) -> str:
        """Graphql query string"""
        return self["requestContext"]["queryString"]

    @property
    def operation_name(self) -> Optional[str]:
        """Graphql operation name, optional"""
        return self["requestContext"].get("operationName")

    @property
    def variables(self) -> Dict:
        """Graphql variables"""
        return self["requestContext"]["variables"]


class AppSyncAuthorizerEvent(DictWrapper):
    """AppSync lambda authorizer event

    Documentation:
    -------------
    - https://aws.amazon.com/blogs/mobile/appsync-lambda-auth/
    - https://docs.aws.amazon.com/appsync/latest/devguide/security-authz.html#aws-lambda-authorization
    """

    @property
    def authorization_token(self) -> str:
        """Authorization token"""
        return self["authorizationToken"]

    @property
    def request_context(self) -> AppSyncAuthorizerEventRequestContext:
        """Request context"""
        return AppSyncAuthorizerEventRequestContext(self._data)


class AppSyncAuthorizerResponse:
    """AppSync Lambda authorizer response helper"""

    def __init__(self):
        self._data: Dict = {"isAuthorized": False}

    def authorize(self) -> "AppSyncAuthorizerResponse":
        """Authorize the authorizationToken by setting isAuthorized to True

        "isAuthorized" is a boolean value indicating if the value in authorizationToken
        is authorized to make calls to the GraphQL API. If this value is
        true, execution of the GraphQL API continues. If this value is false,
        an UnauthorizedException is raised
        """
        self._data["isAuthorized"] = True
        return self

    def ttl(self, ttl_orderride: Optional[int] = 0) -> "AppSyncAuthorizerResponse":
        """Set the ttlOverride

        The number of seconds that the response should be cached for. If no value is
        returned, the value from the API (if configured) or the default of 300 seconds
        (five minutes) is used.
        If this is 0, the response is not cached.
        """
        if ttl_orderride is not None:
            self._data["ttlOverride"] = ttl_orderride
        return self

    def resolver_context(self, resolver_context: Dict) -> "AppSyncAuthorizerResponse":
        """A JSON object visible as $ctx.identity.resolverContext in resolver templates

        Warning: The total size of this JSON object must not exceed 5MB.
        """
        self._data["resolverContext"] = resolver_context
        return self

    def denied_fields(self, denied_fields: List[str]) -> "AppSyncAuthorizerResponse":
        """A list of which are forcibly changed to null, even if a value was returned from a resolver.

        Each item is either a fully qualified field ARN in the form of
        arn:aws:appsync:us-east-1:111122223333:apis/GraphQLApiId/types/TypeName/fields/FieldName
        or a short form of TypeName.FieldName. The full ARN form should be used when two APIs
        share a lambda function authorizer and there might be ambiguity between common types
        and fields between the two APIs.
        """
        self._data["deniedFields"] = denied_fields
        return self

    def asdict(self) -> dict:
        """Return the response as a dict"""
        return self._data
