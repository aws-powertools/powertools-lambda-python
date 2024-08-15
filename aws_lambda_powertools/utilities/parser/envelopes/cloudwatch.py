from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.models import CloudWatchLogsModel

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import Model

logger = logging.getLogger(__name__)


class CloudWatchLogsEnvelope(BaseEnvelope):
    """CloudWatch Envelope to extract a list of log records.

    The record's body parameter is a string (after being base64 decoded and gzipped),
    though it can also be a JSON encoded string.
    Regardless of its type it'll be parsed into a BaseModel object.

    Note: The record will be parsed the same way so if model is str
    """

    def parse(self, data: dict[str, Any] | Any | None, model: type[Model]) -> list[Model | None]:
        """Parses records found with model provided

        Parameters
        ----------
        data : dict
            Lambda event to be parsed
        model : type[Model]
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        list
            List of records parsed with model provided
        """
        logger.debug(f"Parsing incoming data with SNS model {CloudWatchLogsModel}")
        parsed_envelope = CloudWatchLogsModel.model_validate(data)
        logger.debug(f"Parsing CloudWatch records in `body` with {model}")
        return [
            self._parse(data=record.message, model=model) for record in parsed_envelope.awslogs.decoded_data.logEvents
        ]
