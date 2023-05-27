from typing import Any, Dict, Literal, Type, Union

from pydantic import BaseModel, Field, HttpUrl


class CustomResourceBaseModel(BaseModel):
    request_type: str = Field(..., alias="RequestType")
    service_token: str = Field(..., alias="ServiceToken")
    response_url: HttpUrl = Field(..., alias="ResponseURL")
    stack_id: str = Field(..., alias="StackId")
    request_id: str = Field(..., alias="RequestId")
    logical_resource_id: str = Field(..., alias="LogicalResourceId")
    resource_type: str = Field(..., alias="ResourceType")
    resource_properties: Union[Dict[str, Any], Type[BaseModel]] = Field(..., alias="ResourceProperties")


class CustomResourceCreateModel(CustomResourceBaseModel):
    request_type: Literal["Create"] = Field(..., alias="RequestType")


class CustomResourceDeleteModel(CustomResourceBaseModel):
    request_type: Literal["Delete"] = Field(..., alias="RequestType")


class CustomResourceUpdateModel(CustomResourceBaseModel):
    request_type: Literal["Update"] = Field(..., alias="RequestType")
    old_resource_properties: Union[Dict[str, Any], Type[BaseModel]] = Field(..., alias="OldResourceProperties")
