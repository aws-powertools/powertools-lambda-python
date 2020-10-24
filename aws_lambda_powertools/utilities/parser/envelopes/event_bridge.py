import logging
from typing import Any, Dict

from ..models import EventBridgeModel
from ..types import Model
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class EventBridgeEnvelope(BaseEnvelope):
    """EventBridge envelope to extract data within detail key"""

    def parse(self, data: Dict[str, Any], model: Model) -> Model:
        """Parses data found with model provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        model : Model
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        Any
            Parsed detail payload with model provided
        """
        logger.debug(f"Parsing incoming data with EventBridge model {EventBridgeModel}")
        parsed_envelope = EventBridgeModel.parse_obj(data)
        logger.debug(f"Parsing event payload in `detail` with {model}")
        return self._parse(data=parsed_envelope.detail, model=model)
