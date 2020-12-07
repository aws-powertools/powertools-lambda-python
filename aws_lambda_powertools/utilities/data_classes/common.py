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


class BaseProxyEvent(DictWrapper):
    @property
    def headers(self) -> Dict[str, str]:
        return self["headers"]

    @property
    def query_string_parameters(self) -> Optional[Dict[str, str]]:
        return self.get("queryStringParameters")

    @property
    def is_base64_encoded(self) -> bool:
        return self.get("isBase64Encoded")

    @property
    def body(self) -> Optional[str]:
        return self.get("body")

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
        if case_sensitive:
            return self.headers.get(name, default_value)

        return next((value for key, value in self.headers.items() if name.lower() == key.lower()), default_value)
