import logging
from typing import Any, Dict, List, Optional, Type, Union, cast

from ..models import KinesisDataStreamModel
from ..types import Model
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class KinesisDataStreamEnvelope(BaseEnvelope):
    """Kinesis Data Stream Envelope to extract array of Records

    The record's data parameter is a base64 encoded string which is parsed into a bytes array,
    though it can also be a JSON encoded string.
    Regardless of its type it'll be parsed into a BaseModel object.

    Note: Records will be parsed the same way so if model is str,
    all items in the list will be parsed as str and not as JSON (and vice versa)
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
        logger.debug(f"Parsing incoming data with Kinesis model {KinesisDataStreamModel}")
        parsed_envelope: KinesisDataStreamModel = KinesisDataStreamModel.parse_obj(data)
        logger.debug(f"Parsing Kinesis records in `body` with {model}")
        models = []
        for record in parsed_envelope.Records:
            # We allow either AWS expected contract (bytes) or a custom Model, see #943
            data = cast(bytes, record.kinesis.data)
            models.append(self._parse(data=data.decode("utf-8"), model=model))
        return models
