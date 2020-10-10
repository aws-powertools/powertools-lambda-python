import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from pydantic import BaseModel, ValidationError

from ..exceptions import SchemaValidationError

logger = logging.getLogger(__name__)


class BaseEnvelope(ABC):
    @staticmethod
    def _parse(event: Union[Dict[str, Any], str], schema: BaseModel) -> Any:
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
