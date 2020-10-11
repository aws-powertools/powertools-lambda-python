import logging
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

from .envelopes.base import BaseEnvelope
from .exceptions import InvalidEnvelopeError, InvalidSchemaTypeError, SchemaValidationError

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def parser(
    handler: Callable[[Dict, Any], Any],
    event: Dict[str, Any],
    context: Dict[str, Any],
    schema: BaseModel,
    envelope: Optional[BaseEnvelope] = None,
) -> Any:
    """Decorator to conduct advanced parsing & validation for lambda handlers events

    As Lambda follows (event, context) signature we can remove some of the boilerplate
    and also capture any exception any Lambda function throws as metadata.
    event will be the parsed and passed as a BaseModel Pydantic class of the input type "schema"
    to the lambda handler.
    event will be extracted from the envelope in case envelope is not None.
    In case envelope is None, the complete event is parsed to match the schema parameter BaseModel definition.
    In case envelope is not None, first the event is parsed as the envelope's schema definition, and the user
    message is extracted and parsed again as the schema parameter's definition.

    Example
    -------
    **Lambda function using validation decorator**

        @parser(schema=MyBusiness, envelope=envelopes.EVENTBRIDGE)
        def handler(event: MyBusiness , context: LambdaContext):
            ...

    Parameters
    ----------
    handler:  input for lambda_handler_decorator, wraps the handler lambda
    event:    AWS event dictionary
    context:  AWS lambda context
    schema:   pydantic BaseModel class. This is the user data schema that will replace the event.
              event parameter will be parsed and a new schema object will be created from it.
    envelope: what envelope to extract the schema from, can be any AWS service that is currently
              supported in the envelopes module. Can be None.

    Raises
    ------
    SchemaValidationError
        When input event does not conform with schema provided
    InvalidSchemaTypeError
        When schema given does not implement BaseModel
    """
    parsed_event = parse(event=event, schema=schema, envelope=envelope)
    logger.debug(f"Calling handler {handler.__name__}")
    return handler(parsed_event, context)


def parse(event: Dict[str, Any], schema: BaseModel, envelope: Optional[BaseEnvelope] = None) -> Any:
    """
    Standalone parse function to conduct advanced parsing & validation for lambda handlers events

    As Lambda follows (event, context) signature we can remove some of the boilerplate
    and also capture any exception any Lambda function throws as metadata.
    event will be the parsed and passed as a BaseModel Pydantic class of the input type "schema"
    to the lambda handler.
    event will be extracted from the envelope in case envelope is not None.
    In case envelope is None, the complete event is parsed to match the schema parameter BaseModel definition.
    In case envelope is not None, first the event is parsed as the envelope's schema definition, and the user
    message is extracted and parsed again as the schema parameter's definition.

    Example
    -------
    **Lambda function using standalone parse**

        def handler(event: MyBusiness , context: LambdaContext):
            parse(event=event, schema=MyBusiness, envelope=envelopes.EVENTBRIDGE)
            ...

    Parameters
    ----------
    event:    AWS event dictionary
    schema:   pydantic BaseModel class. This is the user data schema that will replace the event.
              event parameter will be parsed and a new schema object will be created from it.
    envelope: what envelope to extract the schema from, can be any AWS service that is currently
              supported in the envelopes module. Can be None.

    Raises
    ------
    SchemaValidationError
        When input event does not conform with schema provided
    InvalidSchemaTypeError
        When schema given does not implement BaseModel
    InvalidEnvelopeError
        When envelope given does not implement BaseEnvelope
    """
    if envelope and callable(envelope):
        try:
            logger.debug(f"Parsing and validating event schema with envelope={envelope}")
            return envelope().parse(event=event, schema=schema)
        except AttributeError:
            raise InvalidEnvelopeError(f"Envelope must implement BaseEnvelope, envelope={envelope}")
        except (ValidationError, TypeError) as e:
            raise SchemaValidationError(f"Input event does not conform with schema, envelope={envelope}") from e

    try:
        logger.debug("Parsing and validating event schema; no envelope used")
        return schema.parse_obj(event)
    except (ValidationError, TypeError) as e:
        raise SchemaValidationError("Input event does not conform with schema") from e
    except AttributeError:
        raise InvalidSchemaTypeError("Input schema must implement BaseModel")
