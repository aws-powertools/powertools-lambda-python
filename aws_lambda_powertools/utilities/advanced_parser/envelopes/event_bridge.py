import logging
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.utilities.advanced_parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.advanced_parser.schemas import EventBridgeSchema

logger = logging.getLogger(__name__)


class EventBridgeEnvelope(BaseEnvelope):
    def parse(self, event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        try:
            parsed_envelope = EventBridgeSchema(**event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception received from input eventbridge event")
            raise
        return self._parse_user_dict_schema(parsed_envelope.detail, inbound_schema_model)
