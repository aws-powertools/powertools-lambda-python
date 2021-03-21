import logging
from typing import Any, Dict, List, Optional, Type, Union

from ..models import DynamoDBStreamModel
from ..types import Model
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class DynamoDBStreamEnvelope(BaseEnvelope):
    """DynamoDB Stream Envelope to extract data within NewImage/OldImage

    Note: Values are the parsed models. Images' values can also be None, and
    length of the list is the record's amount in the original event.
    """

    def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: Type[Model]) -> List[Dict[str, Optional[Model]]]:
        """Parses DynamoDB Stream records found in either NewImage and OldImage with model provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        model : Type[Model]
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        List
            List of dictionaries with NewImage and OldImage records parsed with model provided
        """
        logger.debug(f"Parsing incoming data with DynamoDB Stream model {DynamoDBStreamModel}")
        parsed_envelope = DynamoDBStreamModel.parse_obj(data)
        logger.debug(f"Parsing DynamoDB Stream new and old records with {model}")
        return [
            {
                "NewImage": self._parse(data=record.dynamodb.NewImage, model=model),
                "OldImage": self._parse(data=record.dynamodb.OldImage, model=model),
            }
            for record in parsed_envelope.Records
        ]
