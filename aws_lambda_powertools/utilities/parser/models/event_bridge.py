from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from aws_lambda_powertools.utilities.parser.types import Model


class EventBridgeModel(BaseModel):
    version: str
    id: str  # noqa: A003,VNE003
    source: str
    account: str
    time: datetime
    region: str
    resources: List[str]
    detail_type: str = Field(None, alias="detail-type")
    detail: Union[Dict[str, Any], Model]
    replay_name: Optional[str] = Field(None, alias="replay-name")
