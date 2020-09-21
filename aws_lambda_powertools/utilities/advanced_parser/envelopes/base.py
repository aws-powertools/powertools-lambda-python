import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class BaseEnvelope(ABC):
    def _parse_user_dict_schema(self, user_event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        logger.debug("parsing user dictionary schema")
        try:
            return inbound_schema_model(**user_event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception while extracting user custom schema")
            raise

    def _parse_user_json_string_schema(self, user_event: str, inbound_schema_model: BaseModel) -> Any:
        logger.debug("parsing user dictionary schema")
        if inbound_schema_model == str:
            logger.debug("input is string, returning")
            return user_event
        logger.debug("trying to parse as json encoded string")
        try:
            return inbound_schema_model.parse_raw(user_event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception while extracting user custom schema")
            raise

    @abstractmethod
    def parse(self, event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        return NotImplemented


class UserEnvelope(BaseEnvelope):
    def parse(self, event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        try:
            return inbound_schema_model(**event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception received from input user custom envelopes event")
            raise
