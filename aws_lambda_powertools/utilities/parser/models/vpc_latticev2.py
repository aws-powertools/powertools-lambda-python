from __future__ import annotations

from datetime import datetime  # noqa: TCH003

from pydantic import BaseModel, Field, field_validator


class VpcLatticeV2RequestContextIdentity(BaseModel):
    source_vpc_arn: str | None = Field(None, alias="sourceVpcArn")
    get_type: str | None = Field(None, alias="type")
    principal: str | None = Field(None, alias="principal")
    principal_org_id: str | None = Field(None, alias="principalOrgID")
    session_name: str | None = Field(None, alias="sessionName")
    x509_subject_cn: str | None = Field(None, alias="X509SubjectCn")
    x509_issuer_ou: str | None = Field(None, alias="X509IssuerOu")
    x509_san_dns: str | None = Field(None, alias="x509SanDns")
    x509_san_uri: str | None = Field(None, alias="X509SanUri")
    x509_san_name_cn: str | None = Field(None, alias="X509SanNameCn")


class VpcLatticeV2RequestContext(BaseModel):
    service_network_arn: str = Field(alias="serviceNetworkArn")
    service_arn: str = Field(alias="serviceArn")
    target_group_arn: str = Field(alias="targetGroupArn")
    identity: VpcLatticeV2RequestContextIdentity
    region: str
    time_epoch: float = Field(alias="timeEpoch")
    time_epoch_as_datetime: datetime = Field(alias="timeEpoch")

    @field_validator("time_epoch_as_datetime", mode="before")
    def time_epoch_convert_to_miliseconds(cls, value: int):
        return round(int(value) / 1000)


class VpcLatticeV2Model(BaseModel):
    version: str
    path: str
    method: str
    headers: dict[str, str]
    query_string_parameters: dict[str, str] | None = Field(None, alias="queryStringParameters")
    body: str | type[BaseModel] | None = None
    is_base64_encoded: bool | None = Field(None, alias="isBase64Encoded")
    request_context: VpcLatticeV2RequestContext = Field(None, alias="requestContext")
