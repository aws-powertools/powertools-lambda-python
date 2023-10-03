from typing import Dict, Type, Union

from pydantic import BaseModel, Field


class VpcLatticeModel(BaseModel):
    method: str
    raw_path: str
    body: Union[str, Type[BaseModel]]
    is_base64_encoded: bool
    headers: Dict[str, str]
    query_string_parameters: Dict[str, str]


class VpcLatticeV2Model(BaseModel):
    version: str
    path: str
    method: str
    headers: Dict[str, str]
    query_string_parameters: Dict[str, str]
    body: Union[str, Type[BaseModel]]
    is_base64_encoded: bool
    request_context: Dict[str, str] = Field(alias="requestContext")
