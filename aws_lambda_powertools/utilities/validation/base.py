from typing import Dict

import fastjsonschema

from .exceptions import InvalidEnvelopeExpressionError, InvalidSchemaError, SchemaValidationError

try:
    import jmespath
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


def unwrap_event_from_envelope(data: Dict, envelope: str):
    if not jmespath:
        raise ModuleNotFoundError("This feature require aws-lambda-powertools[jmespath] extra package")

    try:
        return jmespath.search(envelope, data)
    except jmespath.exceptions.LexerError as e:
        raise InvalidEnvelopeExpressionError(e)
