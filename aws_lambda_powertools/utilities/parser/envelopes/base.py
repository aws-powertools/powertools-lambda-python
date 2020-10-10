import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from ..exceptions import InvalidEnvelopeError, SchemaValidationError

logger = logging.getLogger(__name__)


class BaseEnvelope(ABC):
    @staticmethod
    def _parse(event: Dict[str, Any], schema: BaseModel) -> Any:
        if event is None:
            logger.debug("Skipping parsing as event is None")
            return event

        try:
            logger.debug("parsing event against schema")
            if isinstance(event, str):
                logger.debug("parsing event as string")
                return schema.parse_raw(event)
            else:
                return schema.parse_obj(event)
        except (ValidationError, TypeError) as e:
            raise SchemaValidationError("Failed to extract custom schema") from e

    @abstractmethod
    def parse(self, event: Dict[str, Any], schema: BaseModel):
        return NotImplemented  # pragma: no cover


def parse_envelope(event: Dict[str, Any], envelope: BaseEnvelope, schema: BaseModel):
    try:
        logger.debug(f"Parsing and validating event schema, envelope={envelope}")
        return envelope().parse(event=event, schema=schema)
    except (TypeError, AttributeError):
        raise InvalidEnvelopeError(f"envelope must be a callable and instance of BaseEnvelope, envelope={envelope}")
