import logging
from typing import Dict, Optional, Union

import fastjsonschema  # type: ignore

from .exceptions import InvalidSchemaFormatError, SchemaValidationError

logger = logging.getLogger(__name__)


def validate_data_against_schema(data: Union[Dict, str], schema: Dict, formats: Optional[Dict] = None):
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
        formats = formats or {}
        fastjsonschema.validate(definition=schema, data=data, formats=formats)
    except (TypeError, AttributeError, fastjsonschema.JsonSchemaDefinitionException) as e:
        raise InvalidSchemaFormatError(f"Schema received: {schema}, Formats: {formats}. Error: {e}")
    except fastjsonschema.JsonSchemaException as e:
        message = f"Failed schema validation. Error: {e.message}, Path: {e.path}, Data: {e.value}"  # noqa: B306, E501
        raise SchemaValidationError(message)
