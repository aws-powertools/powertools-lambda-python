from typing import Dict, Type, Union

from pydantic import BaseModel


class VpcLatticeModel(BaseModel):
    method: str
    raw_path: str
    body: Union[str, Type[BaseModel]]
    is_base64_encoded: bool
    headers: Dict[str, str]
    query_string_parameters: Dict[str, str]
