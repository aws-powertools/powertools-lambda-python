from typing import Any, Dict, Union

from pydantic import BaseModel, Field, HttpUrl

from aws_lambda_powertools.utilities.parser.types import Literal


class CloudFormationCustomResourceBaseModel(BaseModel):
    request_type: str = Field(..., alias="RequestType")
    service_token: str = Field(..., alias="ServiceToken")
    response_url: HttpUrl = Field(..., alias="ResponseURL")
    stack_id: str = Field(..., alias="StackId")
    request_id: str = Field(..., alias="RequestId")
    logical_resource_id: str = Field(..., alias="LogicalResourceId")
    resource_type: str = Field(..., alias="ResourceType")
    resource_properties: Union[Dict[str, Any], BaseModel, None] = Field(None, alias="ResourceProperties")


class CloudFormationCustomResourceCreateModel(CloudFormationCustomResourceBaseModel):
    request_type: Literal["Create"] = Field(..., alias="RequestType")


class CloudFormationCustomResourceDeleteModel(CloudFormationCustomResourceBaseModel):
    request_type: Literal["Delete"] = Field(..., alias="RequestType")


class CloudFormationCustomResourceUpdateModel(CloudFormationCustomResourceBaseModel):
    request_type: Literal["Update"] = Field(..., alias="RequestType")
    old_resource_properties: Union[Dict[str, Any], BaseModel, None] = Field(None, alias="OldResourceProperties")
