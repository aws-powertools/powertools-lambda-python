import logging
from typing import Any, Dict, List, Union

from pydantic import BaseModel

from ..models import SqsModel
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class SqsEnvelope(BaseEnvelope):
    """SQS Envelope to extract array of Records

    The record's body parameter is a string, though it can also be a JSON encoded string.
    Regardless of its type it'll be parsed into a BaseModel object.

    Note: Records will be parsed the same way so if model is str,
    all items in the list will be parsed as str and npt as JSON (and vice versa)
    """

    def parse(self, data: Dict[str, Any], model: Union[BaseModel, str]) -> List[BaseModel]:
        """Parses records found with model provided

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
        parsed_envelope = SqsModel(**data)
        output = []
        for record in parsed_envelope.Records:
            output.append(self._parse(record.body, model))
        return output
