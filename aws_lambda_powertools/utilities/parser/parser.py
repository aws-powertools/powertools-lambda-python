import logging
from typing import Any, Callable, Dict, Optional, Type, overload

from aws_lambda_powertools.utilities.parser.types import EnvelopeModel, EventParserReturnType, Model

from ...middleware_factory import lambda_handler_decorator
from ..typing import LambdaContext
from .envelopes.base import Envelope
from .exceptions import InvalidEnvelopeError, InvalidModelTypeError

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def event_parser(
    handler: Callable[[Any, LambdaContext], EventParserReturnType],
    event: Dict[str, Any],
    context: LambdaContext,
    model: Type[Model],
    envelope: Optional[Type[Envelope]] = None,
) -> EventParserReturnType:
    """Lambda handler decorator to parse & validate events using Pydantic models

    It requires a model that implements Pydantic BaseModel to parse & validate the event.

    When an envelope is given, it'll use the following logic:

    1. Parse the event against the envelope model first e.g. EnvelopeModel(**event)
    2. Envelope will extract a given key to be parsed against the model e.g. event.detail

    This is useful when you need to confirm event wrapper structure, and
    b) selectively extract a portion of your payload for parsing & validation.

    NOTE: If envelope is omitted, the complete event is parsed to match the model parameter BaseModel definition.

    Example
    -------
    **Lambda handler decorator to parse & validate event**

        class Order(BaseModel):
            id: int
            description: str
            ...

        @event_parser(model=Order)
        def handler(event: Order, context: LambdaContext):
            ...

    **Lambda handler decorator to parse & validate event - using built-in envelope**

        class Order(BaseModel):
            id: int
            description: str
            ...

        @event_parser(model=Order, envelope=envelopes.EVENTBRIDGE)
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
    model:   Model
        Your data model that will replace the event.
    envelope: Envelope
        Optional envelope to extract the model from

    Raises
    ------
    ValidationError
        When input event does not conform with model provided
    InvalidModelTypeError
        When model given does not implement BaseModel
    InvalidEnvelopeError
        When envelope given does not implement BaseEnvelope
    """
    parsed_event = parse(event=event, model=model, envelope=envelope) if envelope else parse(event=event, model=model)
    logger.debug(f"Calling handler {handler.__name__}")
    return handler(parsed_event, context)


@overload
def parse(event: Dict[str, Any], model: Type[Model]) -> Model:
    ...  # pragma: no cover


@overload
def parse(event: Dict[str, Any], model: Type[Model], envelope: Type[Envelope]) -> EnvelopeModel:
    ...  # pragma: no cover


def parse(event: Dict[str, Any], model: Type[Model], envelope: Optional[Type[Envelope]] = None):
    """Standalone function to parse & validate events using Pydantic models

    Typically used when you need fine-grained control over error handling compared to event_parser decorator.

    Example
    -------

    **Lambda handler decorator to parse & validate event**

        from aws_lambda_powertools.utilities.parser import ValidationError

        class Order(BaseModel):
            id: int
            description: str
            ...

        def handler(event: Order, context: LambdaContext):
            try:
                parse(model=Order)
            except ValidationError:
                ...

    **Lambda handler decorator to parse & validate event - using built-in envelope**

        class Order(BaseModel):
            id: int
            description: str
            ...

        def handler(event: Order, context: LambdaContext):
            try:
                parse(model=Order, envelope=envelopes.EVENTBRIDGE)
            except ValidationError:
                ...

    Parameters
    ----------
    event:    Dict
        Lambda event to be parsed & validated
    model:   Model
        Your data model that will replace the event
    envelope: Envelope
        Optional envelope to extract the model from

    Raises
    ------
    ValidationError
        When input event does not conform with model provided
    InvalidModelTypeError
        When model given does not implement BaseModel
    InvalidEnvelopeError
        When envelope given does not implement BaseEnvelope
    """
    if envelope and callable(envelope):
        try:
            logger.debug(f"Parsing and validating event model with envelope={envelope}")
            return envelope().parse(data=event, model=model)
        except AttributeError:
            raise InvalidEnvelopeError(f"Envelope must implement BaseEnvelope, envelope={envelope}")

    try:
        logger.debug("Parsing and validating event model; no envelope used")
        if isinstance(event, str):
            return model.parse_raw(event)

        return model.parse_obj(event)
    except AttributeError:
        raise InvalidModelTypeError(f"Input model must implement BaseModel, model={model}")
