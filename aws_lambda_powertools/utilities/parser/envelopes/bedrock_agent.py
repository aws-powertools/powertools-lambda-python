import logging
from typing import Any, Dict, Optional, Type, Union

from ..models import BedrockAgentEventModel
from ..types import Model
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class BedrockAgentEnvelope(BaseEnvelope):
    """Bedrock Agent envelope to extract data within input_text key"""

    def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: Type[Model]) -> Optional[Model]:
        """Parses data found with model provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        model : Type[Model]
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        Optional[Model]
            Parsed detail payload with model provided
        """
        logger.debug(f"Parsing incoming data with Bedrock Agent model {BedrockAgentEventModel}")
        parsed_envelope: BedrockAgentEventModel = BedrockAgentEventModel.parse_obj(data)
        logger.debug(f"Parsing event payload in `input_text` with {model}")
        return self._parse(data=parsed_envelope.input_text, model=model)
