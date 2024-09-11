from __future__ import annotations

from functools import cached_property
from typing import Any

from aws_lambda_powertools.shared.headers_serializer import (
    BaseHeadersSerializer,
    HttpApiHeadersSerializer,
)
from aws_lambda_powertools.utilities.data_classes.common import (
    BaseProxyEvent,
    CaseInsensitiveDict,
    DictWrapper,
)
from aws_lambda_powertools.utilities.data_classes.shared_functions import base64_decode


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
    def headers(self) -> dict[str, str]:
        """The VPC Lattice event headers."""
        return CaseInsensitiveDict(self["headers"])

    @property
    def decoded_body(self) -> str:
        """Dynamically base64 decode body as a str"""
        body: str = self["body"]
        return base64_decode(body) if self.is_base64_encoded else body

    @property
    def method(self) -> str:
        """The VPC Lattice method used. Valid values include: DELETE, GET, HEAD, OPTIONS, PATCH, POST, and PUT."""
        return self["method"]

    @property
    def http_method(self) -> str:
        """The HTTP method used. Valid values include: DELETE, GET, HEAD, OPTIONS, PATCH, POST, and PUT."""
        return self["method"]

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
    def query_string_parameters(self) -> dict[str, str]:
        """The request query string parameters."""
        return self["query_string_parameters"]

    @cached_property
    def resolved_headers_field(self) -> dict[str, Any]:
        return CaseInsensitiveDict((k, v.split(",") if "," in v else v) for k, v in self.headers.items())


class vpcLatticeEventV2Identity(DictWrapper):
    @property
    def source_vpc_arn(self) -> str | None:
        """The VPC Lattice v2 Event requestContext Identity sourceVpcArn"""
        return self.get("sourceVpcArn")

    @property
    def get_type(self) -> str | None:
        """The VPC Lattice v2 Event requestContext Identity type"""
        return self.get("type")

    @property
    def principal(self) -> str | None:
        """The VPC Lattice v2 Event requestContext principal"""
        return self.get("principal")

    @property
    def principal_org_id(self) -> str | None:
        """The VPC Lattice v2 Event requestContext principalOrgID"""
        return self.get("principalOrgID")

    @property
    def session_name(self) -> str | None:
        """The VPC Lattice v2 Event requestContext sessionName"""
        return self.get("sessionName")

    @property
    def x509_subject_cn(self) -> str | None:
        """The VPC Lattice v2 Event requestContext X509SubjectCn"""
        return self.get("X509SubjectCn")

    @property
    def x509_issuer_ou(self) -> str | None:
        """The VPC Lattice v2 Event requestContext X509IssuerOu"""
        return self.get("X509IssuerOu")

    @property
    def x509_san_dns(self) -> str | None:
        """The VPC Lattice v2 Event requestContext X509SanDns"""
        return self.get("x509SanDns")

    @property
    def x509_san_uri(self) -> str | None:
        """The VPC Lattice v2 Event requestContext X509SanUri"""
        return self.get("X509SanUri")

    @property
    def x509_san_name_cn(self) -> str | None:
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
    def is_base64_encoded(self) -> bool | None:
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

    @cached_property
    def query_string_parameters(self) -> dict[str, str]:
        """The request query string parameters.

        For VPC Lattice V2, the queryStringParameters will contain a dict[str, list[str]]
        so to keep compatibility with existing utilities, we merge all the values with a comma.
        """
        params = self.get("queryStringParameters") or {}
        return {k: ",".join(v) for k, v in params.items()}

    @property
    def resolved_headers_field(self) -> dict[str, str]:
        if self.headers is not None:
            return {key.lower(): value for key, value in self.headers.items()}

        return {}
