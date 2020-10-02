import logging
from typing import Any, Dict, List
from typing_extensions import Literal

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.utilities.advanced_parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.advanced_parser.schemas import DynamoDBSchema

logger = logging.getLogger(__name__)


# returns a List of dictionaries which each contains two keys, "NewImage" and "OldImage".
# The values are the parsed schema models. The images' values can also be None.
# Length of the list is the record's amount in the original event.
class DynamoDBEnvelope(BaseEnvelope):
    def parse(self, event: Dict[str, Any], schema: BaseModel) -> List[Dict[Literal["NewImage", "OldImage"], BaseModel]]:
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
