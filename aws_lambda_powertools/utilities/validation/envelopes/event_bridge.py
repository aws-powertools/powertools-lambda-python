import logging
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from ..schemas import EventBridgeSchema
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class EventBridgeEnvelope(BaseEnvelope):
    def parse(self, event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        try:
            parsed_envelope = EventBridgeSchema(**event)
        except (ValidationError, TypeError):
            logger.exception("Valdation exception received from input eventbridge event")
            raise
        return self._parse_user_dict_schema(parsed_envelope.detail, inbound_schema_model)
