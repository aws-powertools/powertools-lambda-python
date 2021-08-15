from typing import Any, Dict, List, Optional

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
    """AppSync Lambda authorizer response helper

    Parameters
    ----------
    authorize: bool
        authorize is a boolean value indicating if the value in authorizationToken
        is authorized to make calls to the GraphQL API. If this value is
        true, execution of the GraphQL API continues. If this value is false,
        an UnauthorizedException is raised
    ttl: Optional[int]
        Set the ttlOverride. The number of seconds that the response should be
        cached for. If no value is returned, the value from the API (if configured)
        or the default of 300 seconds (five minutes) is used. If this is 0, the response
        is not cached.
    resolver_context: Optional[Dict[str, Any]]
        A JSON object visible as `$ctx.identity.resolverContext` in resolver templates
        Warning: The total size of this JSON object must not exceed 5MB.
    denied_fields: Optional[List[str]]
        A list of which are forcibly changed to null, even if a value was returned from a resolver.
        Each item is either a fully qualified field ARN in the form of
        `arn:aws:appsync:us-east-1:111122223333:apis/GraphQLApiId/types/TypeName/fields/FieldName`
        or a short form of TypeName.FieldName. The full ARN form should be used when two APIs
        share a lambda function authorizer and there might be ambiguity between common types
        and fields between the two APIs.
    """

    def __init__(
        self,
        authorize: bool = False,
        ttl: Optional[int] = None,
        resolver_context: Optional[Dict[str, Any]] = None,
        denied_fields: Optional[List[str]] = None,
    ):
        self._data: Dict = {"isAuthorized": authorize}

        if ttl is not None:
            self._data["ttlOverride"] = ttl

        if denied_fields:
            self._data["deniedFields"] = denied_fields

        if resolver_context:
            self._data["resolverContext"] = resolver_context

    def to_dict(self) -> dict:
        """Return the response as a dict"""
        return self._data
