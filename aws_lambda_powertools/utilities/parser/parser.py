import logging
import typing
from typing import Any, Callable, Dict, Optional, Type, overload

from aws_lambda_powertools.utilities.parser.compat import disable_pydantic_v2_warning
from aws_lambda_powertools.utilities.parser.types import EventParserReturnType, Model

from ...middleware_factory import lambda_handler_decorator
from ..typing import LambdaContext
from .envelopes.base import Envelope
from .exceptions import InvalidEnvelopeError, InvalidModelTypeError

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def event_parser(
    handler: Callable[..., EventParserReturnType],
    event: Dict[str, Any],
    context: LambdaContext,
    model: Optional[Type[Model]] = None,
    envelope: Optional[Type[Envelope]] = None,
    **kwargs: Any,
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
        When model given does not implement BaseModel or is not provided
    InvalidEnvelopeError
        When envelope given does not implement BaseEnvelope
    """

    if model is None:
        # The first parameter of a Lambda function is always the event.
        # Get the first parameter's type by using typing.get_type_hints.
        type_hints = typing.get_type_hints(handler)
        if type_hints:
            model = list(type_hints.values())[0]
        if model is None:
            raise InvalidModelTypeError(
                "The model must be provided either as the `model` argument to `event_parser`"
                "or as the type hint of `event` in the handler that it wraps",
            )

    if envelope:
        parsed_event = parse(event=event, model=model, envelope=envelope)
    else:
        parsed_event = parse(event=event, model=model)

    logger.debug(f"Calling handler {handler.__name__}")
    return handler(parsed_event, context, **kwargs)


@overload
def parse(event: Dict[str, Any], model: Type[Model]) -> Model: ...  # pragma: no cover


@overload
def parse(event: Dict[str, Any], model: Type[Model], envelope: Type[Envelope]) -> Model: ...  # pragma: no cover


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
        except AttributeError as exc:
            raise InvalidEnvelopeError(
                f"Error: {str(exc)}. Please ensure that both the Input model and the Envelope inherits from BaseModel,\n"  # noqa E501
                "and your payload adheres to the specified Input model structure.\n"
                f"Envelope={envelope}\nModel={model}",
            )

    try:
        disable_pydantic_v2_warning()
        logger.debug("Parsing and validating event model; no envelope used")
        if isinstance(event, str):
            return model.parse_raw(event)

        return model.parse_obj(event)
    except AttributeError as exc:
        raise InvalidModelTypeError(
            f"Error: {str(exc)}. Please ensure the Input model inherits from BaseModel,\n"
            "and your payload adheres to the specified Input model structure.\n"
            f"Model={model}",
        )
