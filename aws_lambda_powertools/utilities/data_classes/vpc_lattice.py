import base64
from typing import Any, Dict, Optional

from aws_lambda_powertools.utilities.data_classes.common import (
    DictWrapper,
    get_header_value,
)


class VPCLatticeEvent(DictWrapper):
    @property
    def body(self) -> str:
        """The VPC Lattice body."""
        return self["body"]

    @property
    def json_body(self) -> Any:
        """Parses the submitted body as json"""
        if self._json_data is None:
            self._json_data = self._json_deserializer(self.decoded_body)
        return self._json_data

    @property
    def headers(self) -> Dict[str, str]:
        """The VPC Lattice event headers."""
        return self["headers"]

    @property
    def is_base64_encoded(self) -> bool:
        """A boolean flag to indicate if the applicable request payload is Base64-encode"""
        return self["is_base64_encoded"]

    @property
    def decoded_body(self) -> str:
        """Dynamically base64 decode body as a str"""
        body: str = self["body"]
        if self.is_base64_encoded:
            return base64.b64decode(body.encode()).decode()
        return body

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

    def get_query_string_value(self, name: str, default_value: Optional[str] = None) -> Optional[str]:
        """Get query string value by name

        Parameters
        ----------
        name: str
            Query string parameter name
        default_value: str, optional
            Default value if no value was found by name
        Returns
        -------
        str, optional
            Query string parameter value
        """
        params = self.query_string_parameters
        return default_value if params is None else params.get(name, default_value)

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
            Whether to use a case-sensitive look up
        Returns
        -------
        str, optional
            Header value
        """
        return get_header_value(self.headers, name, default_value, case_sensitive)
