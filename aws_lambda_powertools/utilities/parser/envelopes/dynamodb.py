import logging
from typing import Any, Dict, List

from pydantic import BaseModel
from typing_extensions import Literal

from ..schemas import DynamoDBSchema
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class DynamoDBEnvelope(BaseEnvelope):
    """ DynamoDB Stream Envelope to extract data within NewImage/OldImage

    Note: Values are the parsed schema models. Images' values can also be None, and
    length of the list is the record's amount in the original event.
    """

    def parse(self, data: Dict[str, Any], schema: BaseModel) -> List[Dict[Literal["NewImage", "OldImage"], BaseModel]]:
        """Parses DynamoDB Stream records found in either NewImage and OldImage with schema provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        schema : BaseModel
            User schema provided to parse after extracting data using envelope

        Returns
        -------
        List
            List of records parsed with schema provided
        """
        parsed_envelope = DynamoDBSchema(**data)
        output = []
        for record in parsed_envelope.Records:
            output.append(
                {
                    "NewImage": self._parse(record.dynamodb.NewImage, schema),
                    "OldImage": self._parse(record.dynamodb.OldImage, schema),
                }
            )
        # noinspection PyTypeChecker
        return output
