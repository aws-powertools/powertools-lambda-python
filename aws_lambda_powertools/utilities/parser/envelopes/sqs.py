import logging
from typing import Any, Dict, List, Union

from pydantic import BaseModel, ValidationError

from ..schemas import SqsSchema
from .base import BaseEnvelope

logger = logging.getLogger(__name__)


class SqsEnvelope(BaseEnvelope):
    """SQS Envelope to extract array of Records

    The record's body parameter is a string, though it can also be a JSON encoded string.
    Regardless of it's type it'll be parsed into a BaseModel object.

    Note: Records will be parsed the same way so if schema is str,
    all items in the list will be parsed as str and npt as JSON (and vice versa)
    """

    def parse(self, event: Dict[str, Any], schema: Union[BaseModel, str]) -> List[Union[BaseModel, str]]:
        """Parses records found with schema provided

        Parameters
        ----------
        event : Dict
            Lambda event to be parsed
        schema : BaseModel
            User schema provided to parse after extracting data using envelope

        Returns
        -------
        List
            List of records parsed with schema provided
        """
        try:
            parsed_envelope = SqsSchema(**event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception received from input sqs event")
            raise
        output = []
        for record in parsed_envelope.Records:
            output.append(self._parse_user_json_string_schema(record.body, schema))
        return output
