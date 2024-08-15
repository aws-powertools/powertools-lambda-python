from __future__ import annotations

from pydantic import BaseModel


class VpcLatticeModel(BaseModel):
    method: str
    raw_path: str
    body: str | type[BaseModel]
    is_base64_encoded: bool
    headers: dict[str, str]
    query_string_parameters: dict[str, str]
