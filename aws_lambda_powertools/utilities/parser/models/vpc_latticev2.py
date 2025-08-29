from datetime import datetime
from typing import Dict, Optional, Type, Union

from pydantic import BaseModel, Field, field_validator


class VpcLatticeV2RequestContextIdentity(BaseModel):
    source_vpc_arn: Optional[str] = Field(
        None,
        alias="sourceVpcArn",
        description="The ARN of the VPC from which the request originated.",
        examples=["arn:aws:ec2:us-east-2:123456789012:vpc/vpc-0b8276c84697e7339"],
    )
    get_type: Optional[str] = Field(
        None,
        alias="type",
        description="The type of identity making the request.",
        examples=["AWS_IAM", "NONE"],
    )
    principal: Optional[str] = Field(
        None,
        alias="principal",
        description="The principal ARN of the identity making the request.",
        examples=["arn:aws:sts::123456789012:assumed-role/example-role/057d00f8b51257ba3c853a0f248943cf"],
    )
    principal_org_id: Optional[str] = Field(
        None,
        alias="principalOrgID",
        description="The AWS organization ID of the principal.",
        examples=["o-1234567890"],
    )
    session_name: Optional[str] = Field(
        None,
        alias="sessionName",
        description="The session name for assumed role sessions.",
        examples=["057d00f8b51257ba3c853a0f248943cf"],
    )
    x509_subject_cn: Optional[str] = Field(
        None,
        alias="X509SubjectCn",
        description="The X.509 certificate subject common name.",
        examples=["example.com"],
    )
    x509_issuer_ou: Optional[str] = Field(
        None,
        alias="X509IssuerOu",
        description="The X.509 certificate issuer organizational unit.",
        examples=["IT Department"],
    )
    x509_san_dns: Optional[str] = Field(
        None,
        alias="x509SanDns",
        description="The X.509 certificate Subject Alternative Name DNS entry.",
        examples=["example.com"],
    )
    x509_san_uri: Optional[str] = Field(
        None,
        alias="X509SanUri",
        description="The X.509 certificate Subject Alternative Name URI entry.",
        examples=["https://example.com"],
    )
    x509_san_name_cn: Optional[str] = Field(
        None,
        alias="X509SanNameCn",
        description="The X.509 certificate Subject Alternative Name common name.",
        examples=["example.com"],
    )


class VpcLatticeV2RequestContext(BaseModel):
    service_network_arn: str = Field(
        alias="serviceNetworkArn",
        description="The ARN of the VPC Lattice service network.",
        examples=["arn:aws:vpc-lattice:us-east-2:123456789012:servicenetwork/sn-0bf3f2882e9cc805a"],
    )
    service_arn: str = Field(
        alias="serviceArn",
        description="The ARN of the VPC Lattice service that processed the request.",
        examples=["arn:aws:vpc-lattice:us-east-2:123456789012:service/svc-0a40eebed65f8d69c"],
    )
    target_group_arn: str = Field(
        alias="targetGroupArn",
        description="The ARN of the target group that received the request.",
        examples=["arn:aws:vpc-lattice:us-east-2:123456789012:targetgroup/tg-6d0ecf831eec9f09"],
    )
    identity: VpcLatticeV2RequestContextIdentity = Field(description="Identity information about the requester.")
    region: str = Field(
        description="The AWS region where the request was processed.",
        examples=["us-east-2", "us-west-1", "eu-west-1"],
    )
    time_epoch: float = Field(
        alias="timeEpoch",
        description="The request timestamp in epoch microseconds.",
        examples=[1696331543569073],
    )
    time_epoch_as_datetime: datetime = Field(
        alias="timeEpoch",
        description="The request timestamp converted to datetime.",
    )

    @field_validator("time_epoch_as_datetime", mode="before")
    def time_epoch_convert_to_miliseconds(cls, value: int):
        return round(int(value) / 1000)


class VpcLatticeV2Model(BaseModel):
    version: str = Field(description="The version of the VPC Lattice event format.", examples=["2.0"])
    path: str = Field(
        description="The path portion of the request URL.",
        examples=["/newpath", "/api/v1/users", "/health"],
    )
    method: str = Field(
        description="The HTTP method used for the request.",
        examples=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    headers: Dict[str, str] = Field(
        description="The request headers as key-value pairs.",
        examples=[
            {"host": "test-lambda-service.vpc-lattice-svcs.us-east-2.on.aws", "user-agent": "curl/7.64.1"},
            {"content-type": "application/json"},
        ],
    )
    query_string_parameters: Optional[Dict[str, str]] = Field(
        None,
        alias="queryStringParameters",
        description="The query string parameters as key-value pairs.",
        examples=[{"order-id": "1"}, {"page": "2", "limit": "10"}],
    )
    body: Optional[Union[str, Type[BaseModel]]] = Field(
        None,
        description="The request body. Can be a string or a parsed model if content-type allows parsing.",
    )
    is_base64_encoded: Optional[bool] = Field(
        None,
        alias="isBase64Encoded",
        description="Indicates whether the body is base64-encoded.",
        examples=[False, True],
    )
    request_context: VpcLatticeV2RequestContext = Field(
        ...,
        alias="requestContext",
        description="Contains information about the request context, including VPC Lattice service details.",
    )
