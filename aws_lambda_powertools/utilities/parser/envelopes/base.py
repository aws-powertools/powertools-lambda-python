import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from ..exceptions import InvalidEnvelopeError

logger = logging.getLogger(__name__)


class BaseEnvelope(ABC):
    @staticmethod
    def _parse_user_dict_schema(user_event: Dict[str, Any], schema: BaseModel) -> Any:
        if user_event is None:
            return None
        logger.debug("parsing user dictionary schema")
        try:
            return schema(**user_event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception while extracting user custom schema")
            raise

    @staticmethod
    def _parse_user_json_string_schema(user_event: str, schema: BaseModel) -> Any:
        if user_event is None:
            return None
        # this is used in cases where the underlying schema is not a Dict that can be parsed as baseModel
        # but a plain string i.e SQS has plain string payload
        if schema == str:
            logger.debug("input is string, returning")
            return user_event
        logger.debug("trying to parse as json encoded string")
        try:
            return schema.parse_raw(user_event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception while extracting user custom schema")
            raise

    @abstractmethod
    def parse(self, event: Dict[str, Any], schema: BaseModel):
        return NotImplemented


def parse_envelope(event: Dict[str, Any], envelope: BaseEnvelope, schema: BaseModel):
    if not callable(envelope) and not isinstance(BaseEnvelope):
        logger.exception("envelope must be a callable and instance of BaseEnvelope")
        raise InvalidEnvelopeError("envelope must be a callable and instance of BaseEnvelope")
    logger.debug(f"Parsing and validating event schema, envelope={envelope}")
    return envelope().parse(event=event, schema=schema)
