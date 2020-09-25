import logging
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.utilities.advanced_parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.advanced_parser.schemas import DynamoDBSchema

logger = logging.getLogger(__name__)


class DynamoDBEnvelope(BaseEnvelope):
    def parse(self, event: Dict[str, Any], schema: BaseModel) -> Any:
        try:
            parsed_envelope = DynamoDBSchema(**event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception received from input dynamodb stream event")
            raise
        output = []
        for record in parsed_envelope.Records:
            output.append(
                {
                    "NewImage": self._parse_user_dict_schema(record.dynamodb.NewImage, schema),
                    "OldImage": self._parse_user_dict_schema(record.dynamodb.OldImage, schema),
                }
            )
        return output
