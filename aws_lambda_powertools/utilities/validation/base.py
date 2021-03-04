import logging
from typing import Any, Dict, Optional

import fastjsonschema
import jmespath
from jmespath.exceptions import LexerError

from aws_lambda_powertools.shared.jmespath_functions import PowertoolsFunctions

from .exceptions import InvalidEnvelopeExpressionError, InvalidSchemaFormatError, SchemaValidationError

logger = logging.getLogger(__name__)


def validate_data_against_schema(data: Dict, schema: Dict, formats: Optional[Dict] = None):
    """Validate dict data against given JSON Schema

    Parameters
    ----------
    data : Dict
        Data set to be validated
    schema : Dict
        JSON Schema to validate against
    formats: Dict
        Custom formats containing a key (e.g. int64) and a value expressed as regex or callback returning bool

    Raises
    ------
    SchemaValidationError
        When schema validation fails against data set
    InvalidSchemaFormatError
        When JSON schema provided is invalid
    """
    try:
        fastjsonschema.validate(definition=schema, data=data, formats=formats)
    except (TypeError, AttributeError, fastjsonschema.JsonSchemaDefinitionException) as e:
        raise InvalidSchemaFormatError(f"Schema received: {schema}, Formats: {formats}. Error: {e}")
    except fastjsonschema.JsonSchemaException as e:
        message = f"Failed schema validation. Error: {e.message}, Path: {e.path}, Data: {e.value}"  # noqa: B306, E501
        raise SchemaValidationError(message)


def unwrap_event_from_envelope(data: Dict, envelope: str, jmespath_options: Dict) -> Any:
    """Searches data using JMESPath expression

    Parameters
    ----------
    data : Dict
        Data set to be filtered
    envelope : str
        JMESPath expression to filter data against
    jmespath_options : Dict
        Alternative JMESPath options to be included when filtering expr

    Returns
    -------
    Any
        Data found using JMESPath expression given in envelope
    """
    if not jmespath_options:
        jmespath_options = {"custom_functions": PowertoolsFunctions()}

    try:
        logger.debug(f"Envelope detected: {envelope}. JMESPath options: {jmespath_options}")
        return jmespath.search(envelope, data, options=jmespath.Options(**jmespath_options))
    except (LexerError, TypeError, UnicodeError) as e:
        message = f"Failed to unwrap event from envelope using expression. Error: {e} Exp: {envelope}, Data: {data}"  # noqa: B306, E501
        raise InvalidEnvelopeExpressionError(message)
