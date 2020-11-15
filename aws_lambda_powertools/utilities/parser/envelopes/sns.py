import logging
from typing import Any, Dict, List, Optional, Union

from ..models import SnsModel
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

    def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: Model) -> List[Optional[Model]]:
        """Parses records found with model provided

        Parameters
        ----------
        data : Dict
            Lambda event to be parsed
        model : Model
            Data model provided to parse after extracting data using envelope

        Returns
        -------
        List
            List of records parsed with model provided
        """
        logger.debug(f"Parsing incoming data with SNS model {SnsModel}")
        parsed_envelope = SnsModel.parse_obj(data)
        output = []
        logger.debug(f"Parsing SNS records in `body` with {model}")
        for record in parsed_envelope.Records:
            output.append(self._parse(data=record.Sns.Message, model=model))
        return output
