import logging
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ValidationError

from ...middleware_factory import lambda_handler_decorator
from ..typing import LambdaContext
from .envelopes.base import BaseEnvelope
from .exceptions import InvalidEnvelopeError, InvalidSchemaTypeError, SchemaValidationError

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def event_parser(
    handler: Callable[[Dict, Any], Any],
    event: Dict[str, Any],
    context: LambdaContext,
    schema: BaseModel,
    envelope: Optional[BaseEnvelope] = None,
) -> Any:
    """Lambda handler decorator to parse & validate events using Pydantic models

    It requires a schema that implements Pydantic BaseModel to parse & validate the event.

    When an envelope is given, it'll use the following logic:

    1. Parse the event against envelope schema first e.g. EnvelopeSchema(**event)
    2. Envelope will extract a given key to be parsed against the schema e.g. event.detail

    This is useful when you need to confirm event wrapper structure, and
    b) selectively extract a portion of your payload for parsing & validation.

    NOTE: If envelope is omitted, the complete event is parsed to match the schema parameter BaseModel definition.

    Example
    -------
    **Lambda handler decorator to parse & validate event**

        class Order(BaseModel):
            id: int
            description: str
            ...

        @event_parser(schema=Order)
        def handler(event: Order, context: LambdaContext):
            ...

    **Lambda handler decorator to parse & validate event - using built-in envelope**

        class Order(BaseModel):
            id: int
            description: str
            ...

        @event_parser(schema=Order, envelope=envelopes.EVENTBRIDGE)
        def handler(event: Order, context: LambdaContext):
            ...

    Parameters
    ----------
    handler:  Callable
        Method to annotate on
    event:    Dict
        Lambda event to be parsed & validated
    context:  LambdaContext
        Lambda context object
    schema:   BaseModel
        Your data schema that will replace the event.
    envelope: BaseEnvelope
        Optional envelope to extract the schema from

    Raises
    ------
    SchemaValidationError
        When input event does not conform with schema provided
    InvalidSchemaTypeError
        When schema given does not implement BaseModel
    InvalidEnvelopeError
        When envelope given does not implement BaseEnvelope
    """
    parsed_event = parse(event=event, schema=schema, envelope=envelope)
    logger.debug(f"Calling handler {handler.__name__}")
    return handler(parsed_event, context)


def parse(event: Dict[str, Any], schema: BaseModel, envelope: Optional[BaseEnvelope] = None) -> Any:
    """Standalone function to parse & validate events using Pydantic models

    Typically used when you need fine-grained control over error handling compared to event_parser decorator.

    Example
    -------

    **Lambda handler decorator to parse & validate event**

        from aws_lambda_powertools.utilities.parser.exceptions import SchemaValidationError

        class Order(BaseModel):
            id: int
            description: str
            ...

        def handler(event: Order, context: LambdaContext):
            try:
                parse(schema=Order)
            except SchemaValidationError:
                ...

    **Lambda handler decorator to parse & validate event - using built-in envelope**

        class Order(BaseModel):
            id: int
            description: str
            ...

        def handler(event: Order, context: LambdaContext):
            try:
                parse(schema=Order, envelope=envelopes.EVENTBRIDGE)
            except SchemaValidationError:
                ...

    Parameters
    ----------
    event:    Dict
        Lambda event to be parsed & validated
    schema:   BaseModel
        Your data schema that will replace the event.
    envelope: BaseEnvelope
        Optional envelope to extract the schema from

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
            return envelope().parse(data=event, schema=schema)
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
