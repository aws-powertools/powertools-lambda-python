from typing import Any, Dict, Optional, overload

from aws_lambda_powertools.shared.headers_serializer import (
    BaseHeadersSerializer,
    HttpApiHeadersSerializer,
)
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent
from aws_lambda_powertools.utilities.data_classes.shared_functions import (
    base64_decode,
    get_header_value,
    get_query_string_value,
)


class VPCLatticeEvent(BaseProxyEvent):
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
            return base64_decode(body)
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

    # VPCLattice event has no path field
    # Added here for consistency with the BaseProxyEvent class
    @property
    def path(self) -> str:
        return self["raw_path"]

    # VPCLattice event has no http_method field
    # Added here for consistency with the BaseProxyEvent class
    @property
    def http_method(self) -> str:
        """The HTTP method used. Valid values include: DELETE, GET, HEAD, OPTIONS, PATCH, POST, and PUT."""
        return self["method"]

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
        return get_query_string_value(
            query_string_parameters=self.query_string_parameters,
            name=name,
            default_value=default_value,
        )

    @overload
    def get_header_value(
        self,
        name: str,
        default_value: str,
        case_sensitive: Optional[bool] = False,
    ) -> str:
        ...

    @overload
    def get_header_value(
        self,
        name: str,
        default_value: Optional[str] = None,
        case_sensitive: Optional[bool] = False,
    ) -> Optional[str]:
        ...

    def get_header_value(
        self,
        name: str,
        default_value: Optional[str] = None,
        case_sensitive: Optional[bool] = False,
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
        return get_header_value(
            headers=self.headers,
            name=name,
            default_value=default_value,
            case_sensitive=case_sensitive,
        )

    def header_serializer(self) -> BaseHeadersSerializer:
        # When using the VPC Lattice integration, we have multiple HTTP Headers.
        return HttpApiHeadersSerializer()
