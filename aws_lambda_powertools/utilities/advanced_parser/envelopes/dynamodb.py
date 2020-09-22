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
            parsed_new_image = (
                None if not record.dynamodb.NewImage else self._parse_user_dict_schema(record.dynamodb.NewImage, schema)
            )  # noqa: E501
            parsed_old_image = (
                None if not record.dynamodb.OldImage else self._parse_user_dict_schema(record.dynamodb.OldImage, schema)
            )  # noqa: E501
            output.append({"NewImage": parsed_new_image, "OldImage": parsed_old_image})
        return output
