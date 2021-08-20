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


class RequestContextClientCert(DictWrapper):
    @property
    def client_cert_pem(self) -> str:
        """Client certificate pem"""
        return self["clientCertPem"]

    @property
    def issuer_dn(self) -> str:
        """Issuer Distinguished Name"""
        return self["issuerDN"]

    @property
    def serial_number(self) -> str:
        """Unique serial number for client cert"""
        return self["serialNumber"]

    @property
    def subject_dn(self) -> str:
        """Subject Distinguished Name"""
        return self["subjectDN"]

    @property
    def validity_not_after(self) -> str:
        """Date when the cert is no longer valid

        eg: Aug  5 00:28:21 2120 GMT"""
        return self["validity"]["notAfter"]

    @property
    def validity_not_before(self) -> str:
        """Cert is not valid before this date

        eg: Aug 29 00:28:21 2020 GMT"""
        return self["validity"]["notBefore"]


class RequestContextV2Http(DictWrapper):
    @property
    def method(self) -> str:
        return self["requestContext"]["http"]["method"]

    @property
    def path(self) -> str:
        return self["requestContext"]["http"]["path"]

    @property
    def protocol(self) -> str:
        """The request protocol, for example, HTTP/1.1."""
        return self["requestContext"]["http"]["protocol"]

    @property
    def source_ip(self) -> str:
        """The source IP address of the TCP connection making the request to API Gateway."""
        return self["requestContext"]["http"]["sourceIp"]

    @property
    def user_agent(self) -> str:
        """The User Agent of the API caller."""
        return self["requestContext"]["http"]["userAgent"]


class BaseRequestContextV2(DictWrapper):
    @property
    def account_id(self) -> str:
        """The AWS account ID associated with the request."""
        return self["requestContext"]["accountId"]

    @property
    def api_id(self) -> str:
        """The identifier API Gateway assigns to your API."""
        return self["requestContext"]["apiId"]

    @property
    def domain_name(self) -> str:
        """A domain name"""
        return self["requestContext"]["domainName"]

    @property
    def domain_prefix(self) -> str:
        return self["requestContext"]["domainPrefix"]

    @property
    def http(self) -> RequestContextV2Http:
        return RequestContextV2Http(self._data)

    @property
    def request_id(self) -> str:
        """The ID that API Gateway assigns to the API request."""
        return self["requestContext"]["requestId"]

    @property
    def route_key(self) -> str:
        """The selected route key."""
        return self["requestContext"]["routeKey"]

    @property
    def stage(self) -> str:
        """The deployment stage of the API request"""
        return self["requestContext"]["stage"]

    @property
    def time(self) -> str:
        """The CLF-formatted request time (dd/MMM/yyyy:HH:mm:ss +-hhmm)."""
        return self["requestContext"]["time"]

    @property
    def time_epoch(self) -> int:
        """The Epoch-formatted request time."""
        return self["requestContext"]["timeEpoch"]

    @property
    def authentication(self) -> Optional[RequestContextClientCert]:
        """Optional when using mutual TLS authentication"""
        client_cert = self["requestContext"].get("authentication", {}).get("clientCert")
        return None if client_cert is None else RequestContextClientCert(client_cert)
