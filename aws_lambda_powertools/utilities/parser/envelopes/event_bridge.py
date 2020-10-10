import logging
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.schemas import EventBridgeSchema

from ..exceptions import SchemaValidationError

logger = logging.getLogger(__name__)


class EventBridgeEnvelope(BaseEnvelope):
    """EventBridge envelope to extract data in detail key"""

    def parse(self, event: Dict[str, Any], schema: BaseModel) -> BaseModel:
        """Parses data found with schema provided

        Parameters
        ----------
        event : Dict
            Lambda event to be parsed
        schema : BaseModel
            User schema provided to parse after extracting data using envelope

        Returns
        -------
        Any
            Parsed detail payload with schema provided

        Raises
        ------
        SchemaValidationError
            When input event doesn't conform with schema provided
        """
        try:
            parsed_envelope = EventBridgeSchema(**event)
            return self._parse(parsed_envelope.detail, schema)
        except ValidationError as e:
            raise SchemaValidationError("EventBridge input doesn't conform with schema") from e
