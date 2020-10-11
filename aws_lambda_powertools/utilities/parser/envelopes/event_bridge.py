import logging
from typing import Any, Dict

from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.schemas import EventBridgeSchema

logger = logging.getLogger(__name__)


class EventBridgeEnvelope(BaseEnvelope):
    """EventBridge envelope to extract data within detail key"""

    def parse(self, data: Dict[str, Any], schema: BaseModel) -> BaseModel:
        """Parses data found with schema provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        schema : BaseModel
            User schema provided to parse after extracting data using envelope

        Returns
        -------
        Any
            Parsed detail payload with schema provided
        """
        parsed_envelope = EventBridgeSchema(**data)
        return self._parse(data=parsed_envelope.detail, schema=schema)
