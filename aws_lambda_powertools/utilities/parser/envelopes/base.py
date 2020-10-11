import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseEnvelope(ABC):
    """ABC implementation for creating a supported Envelope"""

    @staticmethod
    def _parse(data: Union[Dict[str, Any], str], schema: BaseModel) -> Any:
        """Parses envelope data against schema provided

        Parameters
        ----------
        data : Dict
            Data to be parsed and validated
        schema
            Schema to parse and validate data against

        Returns
        -------
        Any
            Parsed data
        """
        if data is None:
            logger.debug("Skipping parsing as event is None")
            return data

        logger.debug("parsing event against schema")
        if isinstance(data, str):
            logger.debug("parsing event as string")
            return schema.parse_raw(data)

        return schema.parse_obj(data)

    @abstractmethod
    def parse(self, data: Dict[str, Any], schema: BaseModel):
        """Implementation to parse data against envelope schema, then against the schema

        NOTE: Call `_parse` method to fully parse data with schema provided.

        Example
        -------

        **EventBridge envelope implementation example**

        def parse(...):
            # 1. parses data against envelope schema
            parsed_envelope = EventBridgeSchema(**data)

            # 2. parses portion of data within the envelope against schema
            return self._parse(data=parsed_envelope.detail, schema=schema)
        """
        return NotImplemented  # pragma: no cover
