from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field


class EventBridgeModel(BaseModel):
    version: str
    id: str  # noqa: A003,VNE003
    source: str
    account: str
    time: datetime
    region: str
    resources: List[str]
    detail_type: str = Field(None, alias="detail-type")
    detail: Union[Dict[str, Any], Type[BaseModel]]
    replay_name: Optional[str] = Field(None, alias="replay-name")
