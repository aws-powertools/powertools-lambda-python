import logging
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.utilities.advanced_parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.advanced_parser.schemas import SnsSchema

logger = logging.getLogger(__name__)


class SnsEnvelope(BaseEnvelope):
    def parse(self, event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        try:
            SnsSchema(**event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception received from input sqs event")
            raise
        return None
