from typing import Dict

from aws_lambda_powertools.utilities.data_classes.common import (
    DictWrapper,
)

class VPCLatticeEvent(DictWrapper):
    @property
    def body(self) -> str:
        """The VPC Lattice body."""
        return self["body"]

    @property
    def headers(self) -> Dict[str, str]:
        """The VPC Lattice event headers."""
        return self["headers"]

    @property
    def is_base64_encoded(self) -> bool:
        """A boolean flag to indicate if the applicable request payload is Base64-encode"""
        return self["is_base64_encoded"]

    @property
    def method(self) -> str:
        """The VPC Lattice method used. Valid values include: DELETE, GET, HEAD, OPTIONS, PATCH, POST, and PUT."""
        return self["method"]

    @property
    def query_string_parameters(self) -> Dict[str, str]:
        """The request query string parameters."""
        return self["query_string_parameters"]

    @property
    def raw_path(self) -> str:
        """The raw VPC Lattice request path."""
        return self["raw_path"]
