from functools import cached_property
from typing import Any, Dict, Optional, overload

from aws_lambda_powertools.shared.headers_serializer import (
    BaseHeadersSerializer,
    HttpApiHeadersSerializer,
)
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent, DictWrapper
from aws_lambda_powertools.utilities.data_classes.shared_functions import (
    base64_decode,
    get_header_value,
    get_query_string_value,
)


class VPCLatticeEventBase(BaseProxyEvent):
    @property
    def body(self) -> str:
        """The VPC Lattice body."""
        return self["body"]

    @cached_property
    def json_body(self) -> Any:
        """Parses the submitted body as json"""
        return self._json_deserializer(self.decoded_body)

    @property
    def headers(self) -> Dict[str, str]:
        """The VPC Lattice event headers."""
        return self["headers"]

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
    def http_method(self) -> str:
        """The HTTP method used. Valid values include: DELETE, GET, HEAD, OPTIONS, PATCH, POST, and PUT."""
        return self["method"]

    @overload
    def get_query_string_value(self, name: str, default_value: str) -> str: ...

    @overload
    def get_query_string_value(self, name: str, default_value: Optional[str] = None) -> Optional[str]: ...

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
        case_sensitive: bool = False,
    ) -> str: ...

    @overload
    def get_header_value(
        self,
        name: str,
        default_value: Optional[str] = None,
        case_sensitive: bool = False,
    ) -> Optional[str]: ...

    def get_header_value(
        self,
        name: str,
        default_value: Optional[str] = None,
        case_sensitive: bool = False,
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


class VPCLatticeEvent(VPCLatticeEventBase):
    @property
    def raw_path(self) -> str:
        """The raw VPC Lattice request path."""
        return self["raw_path"]

    @property
    def is_base64_encoded(self) -> bool:
        """A boolean flag to indicate if the applicable request payload is Base64-encode"""
        return self["is_base64_encoded"]

    # VPCLattice event has no path field
    # Added here for consistency with the BaseProxyEvent class
    @property
    def path(self) -> str:
        return self["raw_path"]

    @property
    def query_string_parameters(self) -> Dict[str, str]:
        """The request query string parameters."""
        return self["query_string_parameters"]

    @property
    def resolved_headers_field(self) -> Dict[str, Any]:
        if self.headers is not None:
            headers = {key.lower(): value.split(",") if "," in value else value for key, value in self.headers.items()}
            return headers

        return {}


class vpcLatticeEventV2Identity(DictWrapper):
    @property
    def source_vpc_arn(self) -> Optional[str]:
        """The VPC Lattice v2 Event requestContext Identity sourceVpcArn"""
        return self.get("sourceVpcArn")

    @property
    def get_type(self) -> Optional[str]:
        """The VPC Lattice v2 Event requestContext Identity type"""
        return self.get("type")

    @property
    def principal(self) -> Optional[str]:
        """The VPC Lattice v2 Event requestContext principal"""
        return self.get("principal")

    @property
    def principal_org_id(self) -> Optional[str]:
        """The VPC Lattice v2 Event requestContext principalOrgID"""
        return self.get("principalOrgID")

    @property
    def session_name(self) -> Optional[str]:
        """The VPC Lattice v2 Event requestContext sessionName"""
        return self.get("sessionName")

    @property
    def x509_subject_cn(self) -> Optional[str]:
        """The VPC Lattice v2 Event requestContext X509SubjectCn"""
        return self.get("X509SubjectCn")

    @property
    def x509_issuer_ou(self) -> Optional[str]:
        """The VPC Lattice v2 Event requestContext X509IssuerOu"""
        return self.get("X509IssuerOu")

    @property
    def x509_san_dns(self) -> Optional[str]:
        """The VPC Lattice v2 Event requestContext X509SanDns"""
        return self.get("x509SanDns")

    @property
    def x509_san_uri(self) -> Optional[str]:
        """The VPC Lattice v2 Event requestContext X509SanUri"""
        return self.get("X509SanUri")

    @property
    def x509_san_name_cn(self) -> Optional[str]:
        """The VPC Lattice v2 Event requestContext X509SanNameCn"""
        return self.get("X509SanNameCn")


class vpcLatticeEventV2RequestContext(DictWrapper):
    @property
    def service_network_arn(self) -> str:
        """The VPC Lattice v2 Event requestContext serviceNetworkArn"""
        return self["serviceNetworkArn"]

    @property
    def service_arn(self) -> str:
        """The VPC Lattice v2 Event requestContext serviceArn"""
        return self["serviceArn"]

    @property
    def target_group_arn(self) -> str:
        """The VPC Lattice v2 Event requestContext targetGroupArn"""
        return self["targetGroupArn"]

    @property
    def identity(self) -> vpcLatticeEventV2Identity:
        """The VPC Lattice v2 Event requestContext identity"""
        return vpcLatticeEventV2Identity(self["identity"])

    @property
    def region(self) -> str:
        """The VPC Lattice v2 Event requestContext serviceNetworkArn"""
        return self["region"]

    @property
    def time_epoch(self) -> float:
        """The VPC Lattice v2 Event requestContext timeEpoch"""
        return self["timeEpoch"]


class VPCLatticeEventV2(VPCLatticeEventBase):
    @property
    def version(self) -> str:
        """The VPC Lattice v2 Event version"""
        return self["version"]

    @property
    def is_base64_encoded(self) -> Optional[bool]:
        """A boolean flag to indicate if the applicable request payload is Base64-encode"""
        return self.get("isBase64Encoded")

    @property
    def path(self) -> str:
        """The VPC Lattice v2 Event path"""
        return self["path"]

    @property
    def request_context(self) -> vpcLatticeEventV2RequestContext:
        """The VPC Lattice v2 Event request context."""
        return vpcLatticeEventV2RequestContext(self["requestContext"])

    @property
    def query_string_parameters(self) -> Optional[Dict[str, str]]:
        """The request query string parameters.

        For VPC Lattice V2, the queryStringParameters will contain a Dict[str, List[str]]
        so to keep compatibility with existing utilities, we merge all the values with a comma.
        """
        params = self.get("queryStringParameters")
        if params:
            return {key: ",".join(value) for key, value in params.items()}
        else:
            return None

    @property
    def resolved_headers_field(self) -> Dict[str, str]:
        if self.headers is not None:
            return {key.lower(): value for key, value in self.headers.items()}

        return {}
