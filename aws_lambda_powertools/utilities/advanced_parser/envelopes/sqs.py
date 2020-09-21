import logging
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.utilities.advanced_parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.advanced_parser.schemas import SqsSchema

logger = logging.getLogger(__name__)


class SqsEnvelope(BaseEnvelope):
    def parse(self, event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        try:
            parsed_envelope = SqsSchema(**event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception received from input sqs event")
            raise
        output = []
        for record in parsed_envelope.Records:
            parsed_msg = self._parse_user_json_string_schema(record.body, inbound_schema_model)
            output.append({"body": parsed_msg, "attributes": record.messageAttributes})
        return output
