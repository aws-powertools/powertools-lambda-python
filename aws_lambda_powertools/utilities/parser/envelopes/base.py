import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from ..exceptions import InvalidEnvelopeError, SchemaValidationError

logger = logging.getLogger(__name__)


class BaseEnvelope(ABC):
    @staticmethod
    def _parse_user_dict_schema(user_event: Dict[str, Any], schema: BaseModel) -> Any:
        if user_event is None:
            return None

        try:
            logger.debug("parsing user dictionary schema")
            return schema(**user_event)
        except (ValidationError, TypeError) as e:
            raise SchemaValidationError("Failed to extract custom schema") from e

    @staticmethod
    def _parse_user_json_string_schema(user_event: str, schema: BaseModel) -> Any:
        # this is used in cases where the underlying schema is not a Dict that can be parsed as baseModel
        # but a plain string as payload i.e. SQS: "body": "Test message."
        if schema is str:
            logger.debug("input is string, returning")
            return user_event

        try:
            logger.debug("trying to parse as json encoded string")
            return schema.parse_raw(user_event)
        except (ValidationError, TypeError) as e:
            raise SchemaValidationError("Failed to extract custom schema from JSON string") from e

    @abstractmethod
    def parse(self, event: Dict[str, Any], schema: BaseModel):
        return NotImplemented  # pragma: no cover


def parse_envelope(event: Dict[str, Any], envelope: BaseEnvelope, schema: BaseModel):
    try:
        logger.debug(f"Parsing and validating event schema, envelope={envelope}")
        return envelope().parse(event=event, schema=schema)
    except (TypeError, AttributeError):
        raise InvalidEnvelopeError(f"envelope must be a callable and instance of BaseEnvelope, envelope={envelope}")
