import logging
from typing import Any, Dict, List

from pydantic import BaseModel, ValidationError
from typing_extensions import Literal

from ..exceptions import SchemaValidationError
from ..schemas import DynamoDBSchema
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class DynamoDBEnvelope(BaseEnvelope):
    """ DynamoDB Stream Envelope to extract data within NewImage/OldImage

    Note: Values are the parsed schema models. Images' values can also be None, and
    length of the list is the record's amount in the original event.
    """

    def parse(self, event: Dict[str, Any], schema: BaseModel) -> List[Dict[Literal["NewImage", "OldImage"], BaseModel]]:
        """Parses DynamoDB Stream records found in either NewImage and OldImage with schema provided

        Parameters
        ----------
        event : Dict
            Lambda event to be parsed
        schema : BaseModel
            User schema provided to parse after extracting data using envelope

        Returns
        -------
        List
            List of records parsed with schema provided

        Raises
        ------
        SchemaValidationError
            When input event doesn't conform with schema provided
        """
        try:
            parsed_envelope = DynamoDBSchema(**event)
        except (ValidationError, TypeError) as e:
            raise SchemaValidationError("DynamoDB input doesn't conform with schema") from e

        output = []
        for record in parsed_envelope.Records:
            output.append(
                {
                    "NewImage": self._parse(record.dynamodb.NewImage, schema),
                    "OldImage": self._parse(record.dynamodb.OldImage, schema),
                }
            )
        return output
