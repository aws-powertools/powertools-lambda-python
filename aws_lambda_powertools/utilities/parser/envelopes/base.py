from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

from aws_lambda_powertools.utilities.parser.functions import (
    _parse_and_validate_event,
    _retrieve_or_set_model_from_cache,
)

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import T

logger = logging.getLogger(__name__)


class BaseEnvelope(ABC):
    """ABC implementation for creating a supported Envelope"""

    @staticmethod
    def _parse(data: dict[str, Any] | Any | None, model: type[T]) -> T | None:
        """Parses envelope data against model provided

        Parameters
        ----------
        data : dict
            Data to be parsed and validated
        model : type[T]
            Data model to parse and validate data against

        Returns
        -------
        Any
            Parsed data
        """
        if data is None:
            logger.debug("Skipping parsing as event is None")
            return data

        adapter = _retrieve_or_set_model_from_cache(model=model)

        logger.debug("parsing event against model")
        return _parse_and_validate_event(data=data, adapter=adapter)

    @abstractmethod
    def parse(self, data: dict[str, Any] | Any | None, model: type[T]):
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
