from typing import Any, Dict, List, Optional, Union

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper, get_header_value


def get_identity_object(identity: Optional[dict]) -> Any:
    """Get the identity object based on the best detected type"""
    # API_KEY authorization
    if identity is None:
        return None

    # AMAZON_COGNITO_USER_POOLS authorization
    if "sub" in identity:
        return AppSyncIdentityCognito(identity)

    # AWS_IAM authorization
    return AppSyncIdentityIAM(identity)


class AppSyncIdentityIAM(DictWrapper):
    """AWS_IAM authorization"""

    @property
    def source_ip(self) -> List[str]:
        """The source IP address of the caller received by AWS AppSync. """
        return self["sourceIp"]

    @property
    def username(self) -> str:
        """The user name of the authenticated user. IAM user principal"""
        return self["username"]

    @property
    def account_id(self) -> str:
        """The AWS account ID of the caller."""
        return self["accountId"]

    @property
    def cognito_identity_pool_id(self) -> str:
        """The Amazon Cognito identity pool ID associated with the caller."""
        return self["cognitoIdentityPoolId"]

    @property
    def cognito_identity_id(self) -> str:
        """The Amazon Cognito identity ID of the caller."""
        return self["cognitoIdentityId"]

    @property
    def user_arn(self) -> str:
        """The ARN of the IAM user."""
        return self["userArn"]

    @property
    def cognito_identity_auth_type(self) -> str:
        """Either authenticated or unauthenticated based on the identity type."""
        return self["cognitoIdentityAuthType"]

    @property
    def cognito_identity_auth_provider(self) -> str:
        """A comma separated list of external identity provider information used in obtaining the
        credentials used to sign the request."""
        return self["cognitoIdentityAuthProvider"]


class AppSyncIdentityCognito(DictWrapper):
    """AMAZON_COGNITO_USER_POOLS authorization"""

    @property
    def source_ip(self) -> List[str]:
        """The source IP address of the caller received by AWS AppSync. """
        return self["sourceIp"]

    @property
    def username(self) -> str:
        """The user name of the authenticated user."""
        return self["username"]

    @property
    def sub(self) -> str:
        """The UUID of the authenticated user."""
        return self["sub"]

    @property
    def claims(self) -> Dict[str, str]:
        """The claims that the user has."""
        return self["claims"]

    @property
    def default_auth_strategy(self) -> str:
        """The default authorization strategy for this caller (ALLOW or DENY)."""
        return self["defaultAuthStrategy"]

    @property
    def groups(self) -> List[str]:
        """Array of OIDC groups"""
        return self["groups"]

    @property
    def issuer(self) -> str:
        """The token issuer."""
        return self["issuer"]


class AppSyncResolverEventInfo(DictWrapper):
    """The info section contains information about the GraphQL request"""

    @property
    def field_name(self) -> str:
        """The name of the field that is currently being resolved."""
        return self["fieldName"]

    @property
    def parent_type_name(self) -> str:
        """The name of the parent type for the field that is currently being resolved."""
        return self["parentTypeName"]

    @property
    def variables(self) -> Dict[str, str]:
        """A map which holds all variables that are passed into the GraphQL request."""
        return self["variables"]

    @property
    def selection_set_list(self) -> List[str]:
        """A list representation of the fields in the GraphQL selection set. Fields that are aliased will
        only be referenced by the alias name, not the field name. The following example shows this in detail."""
        return self.get("selectionSetList")

    @property
    def selection_set_graphql(self) -> Optional[str]:
        """A string representation of the selection set, formatted as GraphQL schema definition language (SDL).
        Although fragments are not be merged into the selection set, inline fragments are preserved."""
        return self.get("selectionSetGraphQL")


class AppSyncResolverEvent(DictWrapper):
    """AppSync resolver event

    NOTE: AppSync Resolver Events can come in various shapes this data class supports what
    Amplify GraphQL Transformer produces

    Documentation:
    -------------
    - https://docs.aws.amazon.com/appsync/latest/devguide/resolver-context-reference.html
    - https://docs.amplify.aws/cli/graphql-transformer/function#structure-of-the-function-event
    """

    @property
    def type_name(self) -> str:
        """The name of the parent type for the field that is currently being resolved."""
        return self["typeName"]

    @property
    def field_name(self) -> str:
        """The name of the field that is currently being resolved."""
        return self["fieldName"]

    @property
    def arguments(self) -> Dict[str, any]:
        """A map that contains all GraphQL arguments for this field."""
        return self["arguments"]

    @property
    def identity(self) -> Union[None, AppSyncIdentityIAM, AppSyncIdentityCognito]:
        """An object that contains information about the caller.

        Depending of the type of identify found:

        - API_KEY authorization - returns None
        - AWS_IAM authorization - returns AppSyncIdentityIAM
        - AMAZON_COGNITO_USER_POOLS authorization - returns AppSyncIdentityCognito
        """
        return get_identity_object(self.get("identity"))

    @property
    def source(self) -> Dict[str, any]:
        """A map that contains the resolution of the parent field."""
        return self.get("source")

    @property
    def request_headers(self) -> Dict[str, str]:
        """Request headers"""
        return self["request"]["headers"]

    @property
    def prev_result(self) -> Dict[str, any]:
        """It represents the result of whatever previous operation was executed in a pipeline resolver."""
        return self["prev"]["result"]

    @property
    def info(self) -> Optional[AppSyncResolverEventInfo]:
        """The info section contains information about the GraphQL request.

        NOTE: This is not present for Amplify GraphQL Transformer functions
        """
        info_dict = self.get("info")
        if info_dict is None:
            return None
        return AppSyncResolverEventInfo(info_dict)

    def get_header_value(
        self, name: str, default_value: Optional[str] = None, case_sensitive: Optional[bool] = False
    ) -> Optional[str]:
        """Get header value by name

        Parameters
        ----------
        name: str
            Header name
        default_value: str, optional
            Default value if no value was found by name
        case_sensitive: bool
            Whether to use a case sensitive look up
        Returns
        -------
        str, optional
            Header value
        """
        return get_header_value(self.request_headers, name, default_value, case_sensitive)
