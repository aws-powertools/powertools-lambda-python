import base64
import json
from typing import Any, Dict, Optional


class DictWrapper:
    """Provides a single read only access to a wrapper dict"""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DictWrapper):
            return False

        return self._data == other._data

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    @property
    def raw_event(self) -> Dict[str, Any]:
        """The original raw event dict"""
        return self._data


def get_header_value(
    headers: Dict[str, str], name: str, default_value: Optional[str], case_sensitive: Optional[bool]
) -> Optional[str]:
    """Get header value by name"""
    if case_sensitive:
        return headers.get(name, default_value)

    name_lower = name.lower()

    return next(
        # Iterate over the dict and do a case insensitive key comparison
        (value for key, value in headers.items() if key.lower() == name_lower),
        # Default value is returned if no matches was found
        default_value,
    )


class BaseProxyEvent(DictWrapper):
    @property
    def headers(self) -> Dict[str, str]:
        return self["headers"]

    @property
    def query_string_parameters(self) -> Optional[Dict[str, str]]:
        return self.get("queryStringParameters")

    @property
    def is_base64_encoded(self) -> Optional[bool]:
        return self.get("isBase64Encoded")

    @property
    def body(self) -> Optional[str]:
        """Submitted body of the request as a string"""
        return self.get("body")

    @property
    def json_body(self) -> Any:
        """Parses the submitted body as json"""
        return json.loads(self.decoded_body)

    @property
    def decoded_body(self) -> str:
        """Dynamically base64 decode body as a str"""
        body: str = self["body"]
        if self.is_base64_encoded:
            return base64.b64decode(body.encode()).decode()
        return body

    @property
    def path(self) -> str:
        return self["path"]

    @property
    def http_method(self) -> str:
        """The HTTP method used. Valid values include: DELETE, GET, HEAD, OPTIONS, PATCH, POST, and PUT."""
        return self["httpMethod"]

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
            Whether to use a case sensitive look up
        Returns
        -------
        str, optional
            Header value
        """
        return get_header_value(self.headers, name, default_value, case_sensitive)
