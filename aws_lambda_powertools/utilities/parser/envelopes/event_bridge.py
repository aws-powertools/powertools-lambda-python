import logging
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.schemas import EventBridgeSchema

logger = logging.getLogger(__name__)


# returns a parsed BaseModel object according to schema type
class EventBridgeEnvelope(BaseEnvelope):
    def parse(self, event: Dict[str, Any], schema: BaseModel) -> BaseModel:
        try:
            parsed_envelope = EventBridgeSchema(**event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception received from input eventbridge event")
            raise
        return self._parse_user_dict_schema(parsed_envelope.detail, schema)
