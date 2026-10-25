from __future__ import annotations

import base64
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

OCTET_STREAM = "application/octet-stream"


class EventBridgeV2SystemMetadataModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="aws:EventId", description="Unique event id assigned by the bus.")
    sequence_number: str = Field(alias="aws:SequenceNumber", description="Sequence number of the event in the bus.")
    delivery_type: Literal["LIVE", "REPLAY"] = Field(
        alias="aws:DeliveryType",
        description="Whether the event is delivered live or as part of a replay.",
    )
    ingestion_time: str = Field(alias="aws:IngestionTime", description="Time the bus ingested the event.")
    event_group_id: str | None = Field(None, alias="EventGroupId", description="FIFO group id of the event.")
    deduplication_id: str | None = Field(None, alias="DeduplicationId", description="Deduplication id of the event.")
    content_type: str | None = Field(
        None,
        alias="ContentType",
        description="Content type of the payload.",
        examples=["application/json", "application/eventbridge+json", "application/octet-stream"],
    )
    source: str | None = Field(None, alias="aws:Source", description="Event source, only for PutEvents.")
    detail_type: str | None = Field(None, alias="aws:DetailType", description="Detail type, only for PutEvents.")


class EventBridgeV2RecordModel(BaseModel):
    data: Any = Field(
        alias="Data",
        description="Event payload. Bytes for `application/octet-stream`, the classic envelope for PutEvents.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, alias="Metadata", description="Producer metadata.")
    system_metadata: EventBridgeV2SystemMetadataModel = Field(
        alias="SystemMetadata",
        description="Metadata added by the bus.",
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def decode_octet_stream(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        data = values.get("Data", values.get("data"))
        system_metadata = values.get("SystemMetadata", values.get("system_metadata")) or {}
        content_type = system_metadata.get("ContentType") if isinstance(system_metadata, dict) else None
        if content_type == OCTET_STREAM and isinstance(data, str):
            return {**values, "Data": base64.b64decode(data)}
        return values


class EventBridgeV2Model(RootModel[list[EventBridgeV2RecordModel]]):
    """Amazon EventBridge Custom Event Bus delivery using the WITH_METADATA transformer.

    Accepts a single object or an array, and always exposes a list of records in `root`.
    """

    @model_validator(mode="before")
    @classmethod
    def wrap_single_record(cls, value: Any) -> Any:
        return value if isinstance(value, list) else [value]
