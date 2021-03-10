from typing import Dict

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class AppSyncResolverEvent(DictWrapper):
    """AppSync resolver event

    Documentation:
    -------------
    - https://docs.aws.amazon.com/appsync/latest/devguide/resolver-context-reference.html
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
    def identity(self) -> Dict[str, any]:
        """An object that contains information about the caller."""
        return self["identity"]

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
