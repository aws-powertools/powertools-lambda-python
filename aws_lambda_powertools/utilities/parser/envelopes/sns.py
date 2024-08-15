from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.models import SnsModel, SnsNotificationModel, SqsModel

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.types import Model

logger = logging.getLogger(__name__)


class SnsEnvelope(BaseEnvelope):
    """SNS Envelope to extract array of Records

    The record's body parameter is a string, though it can also be a JSON encoded string.
    Regardless of its type it'll be parsed into a BaseModel object.

    Note: Records will be parsed the same way so if model is str,
    all items in the list will be parsed as str and npt as JSON (and vice versa)
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
        logger.debug(f"Parsing incoming data with SNS model {SnsModel}")
        parsed_envelope = SnsModel.model_validate(data)
        logger.debug(f"Parsing SNS records in `body` with {model}")
        return [self._parse(data=record.Sns.Message, model=model) for record in parsed_envelope.Records]


class SnsSqsEnvelope(BaseEnvelope):
    """SNS plus SQS Envelope to extract array of Records

    Published messages from SNS to SQS has a slightly different payload.
    Since SNS payload is marshalled into `Record` key in SQS, we have to:

    1. Parse SQS schema with incoming data
    2. Unmarshall SNS payload and parse against SNS Notification model not SNS/SNS Record
    3. Finally, parse provided model against payload extracted
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
        logger.debug(f"Parsing incoming data with SQS model {SqsModel}")
        parsed_envelope = SqsModel.model_validate(data)
        output = []
        for record in parsed_envelope.Records:
            # We allow either AWS expected contract (str) or a custom Model, see #943
            body = cast(str, record.body)
            sns_notification = SnsNotificationModel.model_validate_json(body)
            output.append(self._parse(data=sns_notification.Message, model=model))
        return output
