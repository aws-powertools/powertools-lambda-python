import logging
from typing import Dict, Optional, Union

import fastjsonschema  # type: ignore

from aws_lambda_powertools.shared.functions import get_field_or_empty_dict
from aws_lambda_powertools.utilities.validation.exceptions import InvalidSchemaFormatError, SchemaValidationError

logger = logging.getLogger(__name__)


def validate_data_against_schema(
    data: Union[Dict, str],
    schema: Dict,
    formats: Optional[Dict] = None,
    handlers: Optional[Dict] = None,
    provider_options: Optional[Dict] = None,
):
    """Validate dict data against given JSON Schema

    Parameters
    ----------
    data : Dict
        Data set to be validated
    schema : Dict
        JSON Schema to validate against
    formats: Dict
        Custom formats containing a key (e.g. int64) and a value expressed as regex or callback returning bool
    handlers: Dict
        Custom methods to retrieve remote schemes, keyed off of URI scheme
    provider_options: Dict
        Arguments that will be passed directly to the underlying validate call

    Raises
    ------
    SchemaValidationError
        When schema validation fails against data set
    InvalidSchemaFormatError
        When JSON schema provided is invalid
    """
    try:
        formats = get_field_or_empty_dict(formats)
        handlers = get_field_or_empty_dict(handlers)
        provider_options = get_field_or_empty_dict(provider_options)
        fastjsonschema.validate(definition=schema, data=data, formats=formats, handlers=handlers, **provider_options)
    except (TypeError, AttributeError, fastjsonschema.JsonSchemaDefinitionException) as e:
        raise InvalidSchemaFormatError(f"Schema received: {schema}, Formats: {formats}. Error: {e}")
    except fastjsonschema.JsonSchemaValueException as e:
        message = f"Failed schema validation. Error: {e.message}, Path: {e.path}, Data: {e.value}"  # noqa: B306
        raise SchemaValidationError(
            message,
            validation_message=e.message,  # noqa: B306
            name=e.name,
            path=e.path,
            value=e.value,
            definition=e.definition,
            rule=e.rule,
            rule_definition=e.rule_definition,
        )
