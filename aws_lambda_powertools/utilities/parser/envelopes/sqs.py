import logging
from typing import Any, Dict, List, Union

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.utilities.parser.envelopes.base import BaseEnvelope
from aws_lambda_powertools.utilities.parser.schemas import SqsSchema

logger = logging.getLogger(__name__)


# returns a list of parsed schemas of type BaseModel or plain string.
# The record's body parameter is a string. However, it can also be a JSON encoded string which
# can then be parsed into a BaseModel object.
# Note that all records will be parsed the same way so if schema is str,
# all the items in the list will be parsed as str and npt as JSON (and vice versa).
class SqsEnvelope(BaseEnvelope):
    def parse(self, event: Dict[str, Any], schema: Union[BaseModel, str]) -> List[Union[BaseModel, str]]:
        try:
            parsed_envelope = SqsSchema(**event)
        except (ValidationError, TypeError):
            logger.exception("Validation exception received from input sqs event")
            raise
        output = []
        for record in parsed_envelope.Records:
            output.append(self._parse_user_json_string_schema(record.body, schema))
        return output
