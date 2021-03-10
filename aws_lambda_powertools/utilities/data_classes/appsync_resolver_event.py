from typing import Dict, List, Optional, Union

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper, get_header_value


def get_identity_object(identity_object: Optional[dict]) -> any:
    """Get the identity object with the best detected type"""
    # API_KEY authorization
    if identity_object is None:
        return None

    # AMAZON_COGNITO_USER_POOLS authorization
    if "sub" in identity_object:
        return AppSyncIdentityCognito(identity_object)

    # AWS_IAM authorization
    return AppSyncIdentityIAM(identity_object)


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
    def groups(self) -> any:
        return self.get("groups")

    @property
    def issuer(self) -> str:
        """The token issuer."""
        return self["issuer"]


class AppSyncResolverEvent(DictWrapper):
    """AppSync resolver event

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
        """An object that contains information about the caller."""
        return get_identity_object(self["identity"])

    @property
    def source(self) -> Dict[str, any]:
        """A map that contains the resolution of the parent field."""
        return self["source"]

    @property
    def request_headers(self) -> Dict[str, str]:
        """Request headers"""
        return self["request"]["headers"]

    @property
    def prev_result(self) -> Dict[str, any]:
        """It represents the result of whatever previous operation was executed in a pipeline resolver."""
        return self["prev"]["result"]

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
