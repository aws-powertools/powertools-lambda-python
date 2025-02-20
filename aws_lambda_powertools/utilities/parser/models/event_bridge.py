from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

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

    @field_validator("detail", mode="before")
    def validate_detail(cls, v, fields):
        # EventBridge Scheduler sends detail field as '{}' string when no payload is present
        # See: https://github.com/aws-powertools/powertools-lambda-python/issues/6112
        return {} if fields.data.get("source") == "aws.scheduler" and v == "{}" else v
