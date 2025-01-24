from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from aws_lambda_powertools.utilities.parser.types import RawDictOrModel


class EventBridgeModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    version: str
    id: str  # noqa: A003,VNE003
    source: str
    account: str
    time: datetime
    region: str
    resources: List[str]
    detail_type: str = Field(..., alias="detail-type")
    detail: RawDictOrModel
    replay_name: Optional[str] = Field(None, alias="replay-name")
