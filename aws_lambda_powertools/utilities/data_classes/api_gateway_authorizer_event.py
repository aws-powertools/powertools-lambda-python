from typing import Any, Dict, List, Optional

from aws_lambda_powertools.utilities.data_classes.common import BaseRequestContextV2, DictWrapper, get_header_value


class RequestContextV2AuthenticationClientCert(DictWrapper):
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


class RequestContextV2(BaseRequestContextV2):
    @property
    def authentication(self) -> Optional[RequestContextV2AuthenticationClientCert]:
        """Optional when using mutual TLS authentication"""
        authentication = self["requestContext"].get("authentication", {}).get("clientCert")
        return None if authentication is None else RequestContextV2AuthenticationClientCert(authentication)


class ApiGatewayAuthorizerV2Event(DictWrapper):
    """API Gateway Authorizer Format 2.0

    Documentation:
    -------------
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html
    """

    @property
    def version(self) -> str:
        """Event payload version should always be 2.0"""
        return self["version"]

    @property
    def get_type(self) -> str:
        """Event type should always be request"""
        return self["type"]

    @property
    def route_arn(self) -> str:
        """ARN of the route being called

        eg: arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"""
        return self["routeArn"]

    @property
    def identity_source(self) -> Optional[List[str]]:
        """The identity source for which authorization is requested.

        For a REQUEST authorizer, this is optional. The value is a set of one or more mapping expressions of the
        specified request parameters. The identity source can be headers, query string parameters, stage variables,
        and context parameters.
        """
        return self.get("identitySource")

    @property
    def route_key(self) -> str:
        """The route key for the route. For HTTP APIs, the route key can be either $default,
        or a combination of an HTTP method and resource path, for example, GET /pets."""
        return self["routeKey"]

    @property
    def raw_path(self) -> str:
        return self["rawPath"]

    @property
    def raw_query_string(self) -> str:
        return self["rawQueryString"]

    @property
    def cookies(self) -> List[str]:
        return self["cookies"]

    @property
    def headers(self) -> Dict[str, str]:
        return self["headers"]

    @property
    def query_string_parameters(self) -> Dict[str, str]:
        return self["queryStringParameters"]

    @property
    def request_context(self) -> RequestContextV2:
        return RequestContextV2(self._data)

    @property
    def path_parameters(self) -> Optional[Dict[str, str]]:
        return self.get("pathParameters")

    @property
    def stage_variables(self) -> Optional[Dict[str, str]]:
        return self.get("stageVariables")

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


class ApiGatewayAuthorizerSimpleResponse:
    """Api Gateway HTTP API V2 payload authorizer simple response helper

    Parameters
    ----------
    authorize: bool
        authorize is a boolean value indicating if the value in authorizationToken
        is authorized to make calls to the GraphQL API. If this value is
        true, execution of the GraphQL API continues. If this value is false,
        an UnauthorizedException is raised
    context: Dict[str, Any], optional
        A JSON object visible as `event.requestContext.authorizer` lambda event

        The context object only supports key-value pairs. Nested keys are not supported.

        Warning: The total size of this JSON object must not exceed 5MB.
    """

    def __init__(
        self,
        authorize: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.authorize = authorize
        self.context = context

    def asdict(self) -> dict:
        """Return the response as a dict"""
        response: Dict = {"isAuthorized": self.authorize}

        if self.context:
            response["context"] = self.context

        return response
