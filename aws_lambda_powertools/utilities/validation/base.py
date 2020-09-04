import logging
from typing import Dict

import fastjsonschema
import jmespath
from jmespath.exceptions import LexerError

from .exceptions import InvalidEnvelopeExpressionError, InvalidSchemaError, SchemaValidationError
from .jmespath_functions import PowertoolsFunctions

logger = logging.getLogger(__name__)


def validate_data_against_schema(data: Dict, schema: Dict):
    try:
        fastjsonschema.validate(definition=schema, data=data)
    except fastjsonschema.JsonSchemaException as e:
        message = f"Failed inbound validation. Error: {e.message}, Path: {e.path}, Data: {e.value}"  # noqa: B306, E501
        raise SchemaValidationError(message)
    except TypeError as e:
        raise InvalidSchemaError(e)


def unwrap_event_from_envelope(data: Dict, envelope: str, jmespath_options: Dict):
    if not jmespath_options:
        jmespath_options = {"custom_functions": PowertoolsFunctions()}

    try:
        logger.debug(f"Envelope detected: {envelope}. JMESPath options: {jmespath_options}")
        return jmespath.search(envelope, data, options=jmespath.Options(**jmespath_options))
    except LexerError as e:
        raise InvalidEnvelopeExpressionError(e)
