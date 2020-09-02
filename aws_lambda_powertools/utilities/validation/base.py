import json
import logging
from typing import Dict

import fastjsonschema

from .exceptions import InvalidEnvelopeExpressionError, InvalidSchemaError, SchemaValidationError

logger = logging.getLogger(__name__)

try:
    import jmespath

    class PowertoolsJson(jmespath.functions.Functions):
        @jmespath.functions.signature({"types": ["string"]})
        def _func_powertools_json(self, value):
            return json.loads(value)


except ModuleNotFoundError:
    jmespath = None


def validate_data_against_schema(data: Dict, schema: Dict):
    try:
        fastjsonschema.validate(definition=schema, data=data)
    except fastjsonschema.JsonSchemaException as e:
        message = f"Failed inbound validation. Error: {e.message}, Path: {e.path}, Data: {e.value}"  # noqa: B306, E501
        raise SchemaValidationError(message)
    except TypeError as e:
        raise InvalidSchemaError(e)


def unwrap_event_from_envelope(data: Dict, envelope: str, jmespath_options: Dict):
    if not jmespath:
        raise ModuleNotFoundError("This feature require aws-lambda-powertools[jmespath] extra package")

    if not jmespath_options:
        jmespath_options = {"custom_functions": PowertoolsJson()}

    try:
        logger.debug(f"Envelope detected: {envelope}. JMESPath options: {jmespath_options}")
        return jmespath.search(envelope, data, options=jmespath.Options(**jmespath_options))
    except jmespath.exceptions.LexerError as e:
        raise InvalidEnvelopeExpressionError(e)
