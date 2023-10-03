from datetime import datetime
from typing import Dict, Optional, Type, Union

from pydantic import BaseModel, Field


class VpcLatticeV2RequestContextIdentity(BaseModel):
    source_vpc_arn: str = Field(alias="sourceVpcArn")


class VpcLatticeV2RequestContext(BaseModel):
    service_network_arn: str = Field(alias="serviceNetworkArn")
    service_arn: str = Field(alias="serviceArn")
    target_group_arn: str = Field(alias="targetGroupArn")
    identity: VpcLatticeV2RequestContextIdentity
    region: str
    time_epoch: datetime = Field(alias="timeEpoch")


class VpcLatticeV2Model(BaseModel):
    version: str
    path: str
    method: str
    headers: Dict[str, str]
    query_string_parameters: Optional[Dict[str, str]] = None
    body: Optional[Union[str, Type[BaseModel]]] = None
    is_base64_encoded: Optional[bool] = Field(None, alias="isBase64Encoded")
    request_context: VpcLatticeV2RequestContext = Field(None, alias="requestContext")
