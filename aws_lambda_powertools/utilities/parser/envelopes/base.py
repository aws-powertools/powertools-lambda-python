import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseEnvelope(ABC):
    """ABC implementation for creating a supported Envelope"""

    @staticmethod
    def _parse(event: Union[Dict[str, Any], str], schema: BaseModel) -> Any:
        if event is None:
            logger.debug("Skipping parsing as event is None")
            return event

        logger.debug("parsing event against schema")
        if isinstance(event, str):
            logger.debug("parsing event as string")
            return schema.parse_raw(event)

        return schema.parse_obj(event)

    @abstractmethod
    def parse(self, event: Dict[str, Any], schema: BaseModel):
        return NotImplemented  # pragma: no cover
