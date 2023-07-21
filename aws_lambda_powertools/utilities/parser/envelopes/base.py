import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar, Union

from aws_lambda_powertools.utilities.parser.compat import disable_pydantic_v2_warning
from aws_lambda_powertools.utilities.parser.types import Model

logger = logging.getLogger(__name__)


class BaseEnvelope(ABC):
    """ABC implementation for creating a supported Envelope"""

    @staticmethod
    def _parse(data: Optional[Union[Dict[str, Any], Any]], model: Type[Model]) -> Union[Model, None]:
        """Parses envelope data against model provided

        Parameters
        ----------
        data : Dict
            Data to be parsed and validated
        model : Type[Model]
            Data model to parse and validate data against

        Returns
        -------
        Any
            Parsed data
        """
        disable_pydantic_v2_warning()

        if data is None:
            logger.debug("Skipping parsing as event is None")
            return data

        logger.debug("parsing event against model")
        if isinstance(data, str):
            logger.debug("parsing event as string")
            return model.parse_raw(data)

        return model.parse_obj(data)

    @abstractmethod
    def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: Type[Model]):
        """Implementation to parse data against envelope model, then against the data model

        NOTE: Call `_parse` method to fully parse data with model provided.

        Example
        -------

        **EventBridge envelope implementation example**

        def parse(...):
            # 1. parses data against envelope model
            parsed_envelope = EventBridgeModel(**data)

            # 2. parses portion of data within the envelope against model
            return self._parse(data=parsed_envelope.detail, model=data_model)
        """
        return NotImplemented  # pragma: no cover


# Generic to support type annotations throughout parser
# Note: Can't be defined under base.py due to circular dependency
Envelope = TypeVar("Envelope", bound=BaseEnvelope)
