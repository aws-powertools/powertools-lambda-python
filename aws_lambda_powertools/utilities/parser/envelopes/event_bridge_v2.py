from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.models import EventBridgeV2Model

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import T

logger = logging.getLogger(__name__)


def _is_with_metadata(item: Any) -> bool:
    return isinstance(item, dict) and "Data" in item and "SystemMetadata" in item


def _unwrap_put_events(data: Any) -> Any:
    if isinstance(data, dict) and "detail-type" in data and "detail" in data:
        return data["detail"]
    return data


class EventBridgeV2Envelope(BaseEnvelope):
    """EventBridge Custom Event Bus envelope to extract the payload of each record

    Yields `Data` for events published with PutRawEvents, and `Data.detail` for PutEvents.
    RAW deliveries (classic envelope, PutEvents array, bare payload) are also accepted.
    """

    def parse(self, data: dict[str, Any] | Any | None, model: type[T]) -> list[T | None]:
        """Parses records found with model provided

        Parameters
        ----------
        data : dict
            Lambda event to be parsed
        model : type[T]
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        list[T | None]
            List of payloads parsed with model provided
        """
        items = data if isinstance(data, list) else [data]

        payloads: list[Any] = []
        for item in items:
            if _is_with_metadata(item):
                logger.debug(f"Parsing incoming data with EventBridge V2 model {EventBridgeV2Model}")
                payload = EventBridgeV2Model.model_validate(item).root[0].data
            else:
                payload = item
            if isinstance(payload, bytes):
                # application/octet-stream is delivered as bytes; let the JSON path of _parse handle it
                payload = payload.decode()
            payloads.append(_unwrap_put_events(payload))

        logger.debug(f"Parsing EventBridge V2 payloads with {model}")
        return [self._parse(data=payload, model=model) for payload in payloads]
