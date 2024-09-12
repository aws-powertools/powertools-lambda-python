from __future__ import annotations

import logging

import fastjsonschema  # type: ignore

from aws_lambda_powertools.utilities.validation.exceptions import InvalidSchemaFormatError, SchemaValidationError

logger = logging.getLogger(__name__)


def validate_data_against_schema(
    data: dict | str,
    schema: dict,
    formats: dict | None = None,
    handlers: dict | None = None,
    provider_options: dict | None = None,
) -> dict | str:
    """Validate dict data against given JSON Schema

    Parameters
    ----------
    data : dict
        Data set to be validated
    schema : dict
        JSON Schema to validate against
    formats: dict
        Custom formats containing a key (e.g. int64) and a value expressed as regex or callback returning bool
    handlers: Dict
        Custom methods to retrieve remote schemes, keyed off of URI scheme
    provider_options: Dict
        Arguments that will be passed directly to the underlying validation call, in this case fastjsonchema.validate.
        For all supported arguments see: https://horejsek.github.io/python-fastjsonschema/#fastjsonschema.validate

    Returns
    -------
    Dict
        The validated event. If the schema specifies a `default` value for fields that are omitted,
        those default values will be included in the response.

    Raises
    ------
    SchemaValidationError
        When schema validation fails against data set
    InvalidSchemaFormatError
        When JSON schema provided is invalid
    """
    try:
        formats = formats or {}
        handlers = handlers or {}
        provider_options = provider_options or {}
        return fastjsonschema.validate(
            definition=schema,
            data=data,
            formats=formats,
            handlers=handlers,
            **provider_options,
        )
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
