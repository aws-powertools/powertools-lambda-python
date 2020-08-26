from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


class EventBridgeSchema(BaseModel):
    version: str
    id: str  # noqa: A003,VNE003
    source: str
    account: int
    time: datetime
    region: str
    resources: List[str]
    detail: Dict[str, Any]
