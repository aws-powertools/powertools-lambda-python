from __future__ import annotations

import warnings
from typing import Any, overload

from typing_extensions import deprecated

from aws_lambda_powertools.utilities.data_classes.common import CaseInsensitiveDict, DictWrapper
from aws_lambda_powertools.utilities.data_classes.shared_functions import (
    get_header_value,
)
from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning


def get_identity_object(identity: dict | None) -> Any:
    """Get the identity object based on the best detected type"""
    # API_KEY authorization
    if identity is None:
        return None

    # AMAZON_COGNITO_USER_POOLS authorization
    if "sub" in identity:
        return AppSyncIdentityCognito(identity)

    # AWS_IAM authorization
    return AppSyncIdentityIAM(identity)


class AppSyncEventBase(DictWrapper):
    """AppSync resolver event base to work with AppSync GraphQL + Events"""

    @property
    def request_headers(self) -> dict[str, str]:
        """Request headers"""
        return CaseInsensitiveDict(self["request"]["headers"])

    @property
    def domain_name(self) -> str | None:
        """The domain name when using custom domain"""
        return self["request"].get("domainName")

    @property
    def prev_result(self) -> dict[str, Any] | None:
        """It represents the result of whatever previous operation was executed in a pipeline resolver."""
        prev = self.get("prev")
        return prev.get("result") if prev else None

    @property
    def stash(self) -> dict:
        """The stash is a map that is made available inside each resolver and function mapping template.
        The same stash instance lives through a single resolver execution. This means that you can use the
        stash to pass arbitrary data across request and response mapping templates, and across functions in
        a pipeline resolver."""
        return self.get("stash") or {}

    @property
    def identity(self) -> AppSyncIdentityIAM | AppSyncIdentityCognito | None:
        """An object that contains information about the caller.
        Depending on the type of identify found:
        - API_KEY authorization - returns None
        - AWS_IAM authorization - returns AppSyncIdentityIAM
        - AMAZON_COGNITO_USER_POOLS authorization - returns AppSyncIdentityCognito
        - AWS_LAMBDA authorization - returns None - NEED TO TEST
        - OPENID_CONNECT authorization - returns None - NEED TO TEST
        """
        return get_identity_object(self.get("identity"))


class AppSyncIdentityIAM(DictWrapper):
    """AWS_IAM authorization"""

    @property
    def source_ip(self) -> list[str]:
        """The source IP address of the caller received by AWS AppSync."""
        return self["sourceIp"]

    @property
    def username(self) -> str:
        """The username of the authenticated user. IAM user principal"""
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
    def source_ip(self) -> list[str]:
        """The source IP address of the caller received by AWS AppSync."""
        return self["sourceIp"]

    @property
    def username(self) -> str:
        """The username of the authenticated user."""
        return self["username"]

    @property
    def sub(self) -> str:
        """The UUID of the authenticated user."""
        return self["sub"]

    @property
    def claims(self) -> dict[str, str]:
        """The claims that the user has."""
        return self["claims"]

    @property
    def default_auth_strategy(self) -> str:
        """The default authorization strategy for this caller (ALLOW or DENY)."""
        return self["defaultAuthStrategy"]

    @property
    def groups(self) -> list[str]:
        """List of OIDC groups"""
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
    def variables(self) -> dict[str, str]:
        """A map which holds all variables that are passed into the GraphQL request."""
        return self.get("variables") or {}

    @property
    def selection_set_list(self) -> list[str]:
        """A list representation of the fields in the GraphQL selection set. Fields that are aliased will
        only be referenced by the alias name, not the field name."""
        return self.get("selectionSetList") or []

    @property
    def selection_set_graphql(self) -> str | None:
        """A string representation of the selection set, formatted as GraphQL schema definition language (SDL).
        Although fragments are not be merged into the selection set, inline fragments are preserved."""
        return self.get("selectionSetGraphQL")


class AppSyncResolverEvent(AppSyncEventBase):
    """AppSync resolver event

    **NOTE:** AppSync Resolver Events can come in various shapes this data class
    supports both Amplify GraphQL directive @function and Direct Lambda Resolver

    Documentation:
    -------------
    - https://docs.aws.amazon.com/appsync/latest/devguide/resolver-context-reference.html
    - https://docs.amplify.aws/cli/graphql-transformer/function#structure-of-the-function-event
    """

    def __init__(self, data: dict):
        super().__init__(data)

        info: dict | None = data.get("info")
        if not info:
            parent_type_name = self.get("parentTypeName") or self.get("typeName")
            info = {"fieldName": self.get("fieldName"), "parentTypeName": parent_type_name}

        self._info = AppSyncResolverEventInfo(info)

    @property
    def type_name(self) -> str:
        """The name of the parent type for the field that is currently being resolved."""
        return self.info.parent_type_name

    @property
    def field_name(self) -> str:
        """The name of the field that is currently being resolved."""
        return self.info.field_name

    @property
    def arguments(self) -> dict[str, Any]:
        """A map that contains all GraphQL arguments for this field."""
        return self["arguments"]

    @property
    def source(self) -> dict[str, Any]:
        """A map that contains the resolution of the parent field."""
        return self.get("source") or {}

    @property
    def info(self) -> AppSyncResolverEventInfo:
        """The info section contains information about the GraphQL request."""
        return self._info

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
        return get_header_value(self.request_headers, name, default_value, case_sensitive)
