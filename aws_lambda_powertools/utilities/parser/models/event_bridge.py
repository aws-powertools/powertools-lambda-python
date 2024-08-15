from __future__ import annotations

from datetime import datetime  # noqa: TCH003

from pydantic import BaseModel, Field

from aws_lambda_powertools.utilities.parser.types import RawDictOrModel  # noqa: TCH001


class EventBridgeModel(BaseModel):
    version: str
    id: str  # noqa: A003,VNE003
    source: str
    account: str
    time: datetime
    region: str
    resources: list[str]
    detail_type: str = Field(None, alias="detail-type")
    detail: RawDictOrModel
    replay_name: str | None = Field(None, alias="replay-name")
