import logging
from typing import Any, Dict, List

from pydantic import BaseModel
from typing_extensions import Literal

from ..models import DynamoDBStreamModel
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class DynamoDBStreamEnvelope(BaseEnvelope):
    """ DynamoDB Stream Envelope to extract data within NewImage/OldImage

    Note: Values are the parsed models. Images' values can also be None, and
    length of the list is the record's amount in the original event.
    """

    def parse(self, data: Dict[str, Any], model: BaseModel) -> List[Dict[Literal["NewImage", "OldImage"], BaseModel]]:
        """Parses DynamoDB Stream records found in either NewImage and OldImage with model provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        model : BaseModel
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        List
            List of records parsed with model provided


        """
        parsed_envelope = DynamoDBStreamModel(**data)
        output = []
        for record in parsed_envelope.Records:
            output.append(
                {
                    "NewImage": self._parse(record.dynamodb.NewImage, model),
                    "OldImage": self._parse(record.dynamodb.OldImage, model),
                }
            )
        # noinspection PyTypeChecker
        return output
