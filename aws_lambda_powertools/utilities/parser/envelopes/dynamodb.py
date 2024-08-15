from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.models import DynamoDBStreamModel

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import Model

logger = logging.getLogger(__name__)


class DynamoDBStreamEnvelope(BaseEnvelope):
    """DynamoDB Stream Envelope to extract data within NewImage/OldImage

    Note: Values are the parsed models. Images' values can also be None, and
    length of the list is the record's amount in the original event.
    """

    def parse(self, data: dict[str, Any] | Any | None, model: type[Model]) -> list[dict[str, Model | None]]:
        """Parses DynamoDB Stream records found in either NewImage and OldImage with model provided

        Parameters
        ----------
        data : dict
            Lambda event to be parsed
        model : type[Model]
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        list
            List of dictionaries with NewImage and OldImage records parsed with model provided
        """
        logger.debug(f"Parsing incoming data with DynamoDB Stream model {DynamoDBStreamModel}")
        parsed_envelope = DynamoDBStreamModel.model_validate(data)
        logger.debug(f"Parsing DynamoDB Stream new and old records with {model}")
        return [
            {
                "NewImage": self._parse(data=record.dynamodb.NewImage, model=model),
                "OldImage": self._parse(data=record.dynamodb.OldImage, model=model),
            }
            for record in parsed_envelope.Records
        ]
