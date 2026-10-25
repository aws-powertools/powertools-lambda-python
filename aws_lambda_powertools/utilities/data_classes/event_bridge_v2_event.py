from __future__ import annotations

import base64
from functools import cached_property
from typing import Any, Literal

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper

OCTET_STREAM = "application/octet-stream"


def _is_with_metadata(item: Any) -> bool:
    return isinstance(item, dict) and "Data" in item and "SystemMetadata" in item


class EventBridgeV2SystemMetadata(DictWrapper):
    """Metadata added by the bus (`SystemMetadata`), only present with the WITH_METADATA transformer"""

    @property
    def event_id(self) -> str | None:
        """Unique event id assigned by the bus (`aws:EventId`). It is not the id of the classic envelope."""
        return self.get("aws:EventId")

    @property
    def sequence_number(self) -> str | None:
        """Sequence number of the event within the bus (`aws:SequenceNumber`)."""
        return self.get("aws:SequenceNumber")

    @property
    def delivery_type(self) -> Literal["LIVE", "REPLAY"] | None:
        """Whether the event is delivered as it arrives (`LIVE`) or as part of a replay (`REPLAY`)."""
        return self.get("aws:DeliveryType")

    @property
    def ingestion_time(self) -> str | None:
        """Time the bus ingested the event (`aws:IngestionTime`)."""
        return self.get("aws:IngestionTime")

    @property
    def event_group_id(self) -> str | None:
        """FIFO group id the event belongs to (`EventGroupId`)."""
        return self.get("EventGroupId")

    @property
    def deduplication_id(self) -> str | None:
        """Deduplication id of the event (`DeduplicationId`)."""
        return self.get("DeduplicationId")

    @property
    def content_type(self) -> str | None:
        """Content type of the payload, e.g. `application/json` or `application/eventbridge+json` (`ContentType`)."""
        return self.get("ContentType")

    @property
    def source(self) -> str | None:
        """Event source (`aws:Source`), only present for events published with PutEvents."""
        return self.get("aws:Source")

    @property
    def detail_type(self) -> str | None:
        """Event detail type (`aws:DetailType`), only present for events published with PutEvents."""
        return self.get("aws:DetailType")


class EventBridgeV2Record(DictWrapper):
    """A single event delivered by an Amazon EventBridge Custom Event Bus"""

    @property
    def data(self) -> Any:
        """Event payload: a dict for JSON, bytes for `application/octet-stream`."""
        data = self["Data"]
        if self.system_metadata.content_type == OCTET_STREAM and isinstance(data, str):
            return base64.b64decode(data)
        return data

    @property
    def detail(self) -> dict[str, Any] | None:
        """Shortcut to `data["detail"]` when the event was published with PutEvents, otherwise None."""
        data = self["Data"]
        if isinstance(data, dict) and "detail-type" in data and "detail" in data:
            return data["detail"]
        return None

    @property
    def metadata(self) -> dict[str, Any]:
        """Producer metadata keys sent with PutRawEvents."""
        return self.get("Metadata") or {}

    @cached_property
    def system_metadata(self) -> EventBridgeV2SystemMetadata:
        """Metadata added by the bus; empty when the subscriber doesn't use the WITH_METADATA transformer."""
        return EventBridgeV2SystemMetadata(self.get("SystemMetadata") or {})


class EventBridgeV2Event(DictWrapper):
    """Amazon EventBridge Custom Event Bus event

    Accepts what a subscriber can deliver to Lambda: a single object or an array, using the
    WITH_METADATA transformer (`Data`, `Metadata`, `SystemMetadata`) or RAW (classic envelope,
    PutEvents array or the bare PutRawEvents payload). RAW deliveries carry no marker, so
    they are exposed with empty metadata.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-custom-event-bus.html
    """

    @cached_property
    def records(self) -> list[EventBridgeV2Record]:
        """Events in the delivery. Always a list, even when the bus sent a single object."""
        items = self._data if isinstance(self._data, list) else [self._data]
        return [
            EventBridgeV2Record(
                item if _is_with_metadata(item) else {"Data": item, "Metadata": {}, "SystemMetadata": {}},
            )
            for item in items
        ]
