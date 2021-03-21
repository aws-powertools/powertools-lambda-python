import logging
from typing import Any, Dict, List, Optional, Type, Union

from ..models import SnsModel, SnsNotificationModel, SqsModel
from ..types import Model
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class SnsEnvelope(BaseEnvelope):
    """SNS Envelope to extract array of Records

    The record's body parameter is a string, though it can also be a JSON encoded string.
    Regardless of its type it'll be parsed into a BaseModel object.

    Note: Records will be parsed the same way so if model is str,
    all items in the list will be parsed as str and npt as JSON (and vice versa)
    """

    def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: Type[Model]) -> List[Optional[Model]]:
        """Parses records found with model provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        model : Type[Model]
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        List
            List of records parsed with model provided
        """
        logger.debug(f"Parsing incoming data with SNS model {SnsModel}")
        parsed_envelope = SnsModel.parse_obj(data)
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

    def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: Type[Model]) -> List[Optional[Model]]:
        """Parses records found with model provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        model : Type[Model]
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        List
            List of records parsed with model provided
        """
        logger.debug(f"Parsing incoming data with SQS model {SqsModel}")
        parsed_envelope = SqsModel.parse_obj(data)
        output = []
        for record in parsed_envelope.Records:
            sns_notification = SnsNotificationModel.parse_raw(record.body)
            output.append(self._parse(data=sns_notification.Message, model=model))
        return output
