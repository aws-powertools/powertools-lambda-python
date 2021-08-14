from typing import Optional

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
    def variables(self) -> dict:
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
