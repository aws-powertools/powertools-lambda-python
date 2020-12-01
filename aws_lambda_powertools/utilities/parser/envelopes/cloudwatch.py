import logging
from typing import Any, Dict, List, Optional, Union

from ..models import CloudWatchLogsModel
from ..types import Model
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class CloudatchLogsEnvelope(BaseEnvelope):
    """Cloudatch Envelope to extract a List of log records.

    The record's body parameter is a string (after being base64 decoded and gzipped), 
    though it can also be a JSON encoded string.
    Regardless of its type it'll be parsed into a BaseModel object.

    Note: The record will be parsed the same way so if model is str
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
        logger.debug(f"Parsing incoming data with SNS model {CloudWatchLogsModel}")
        parsed_envelope = CloudWatchLogsModel.parse_obj(data)
        logger.debug(f"Parsing CloudWatch records in `body` with {model}")
        output = []
        for record in parsed_envelope.awslogs.decoded_data.logEvents:
            output.append(self._parse(data=record.message, model=model))
        return output
