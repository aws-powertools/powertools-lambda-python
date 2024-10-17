from __future__ import annotations

import logging
import typing
from typing import TYPE_CHECKING, Any, Callable, overload

from pydantic import PydanticSchemaGenerationError

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.parser.exceptions import InvalidEnvelopeError, InvalidModelTypeError
from aws_lambda_powertools.utilities.parser.functions import (
    _parse_and_validate_event,
    _retrieve_or_set_model_from_cache,
)

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser.envelopes.base import Envelope
    from aws_lambda_powertools.utilities.parser.types import EventParserReturnType, T
    from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def event_parser(
    handler: Callable[..., EventParserReturnType],
    event: dict[str, Any],
    context: LambdaContext,
    model: type[T] | None = None,
    envelope: type[Envelope] | None = None,
    **kwargs: Any,
) -> EventParserReturnType:
    """Lambda handler decorator to parse & validate events using Pydantic models

    It requires a model that implements Pydantic BaseModel to parse & validate the event.

    When an envelope is given, it'll use the following logic:

    1. Parse the event against the envelope model first e.g. EnvelopeModel(**event)
    2. Envelope will extract a given key to be parsed against the model e.g. event.detail

    This is useful when you need to confirm event wrapper structure, and
    b) selectively extract a portion of your payload for parsing & validation.

    NOTE: If envelope is omitted, the complete event is parsed to match the model parameter definition.

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
    event:    dict
        Lambda event to be parsed & validated
    context:  LambdaContext
        Lambda context object
    model:   type[T] | None
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

    try:
        if envelope:
            parsed_event = parse(event=event, model=model, envelope=envelope)
        else:
            parsed_event = parse(event=event, model=model)

        logger.debug(f"Calling handler {handler.__name__}")
        return handler(parsed_event, context, **kwargs)
    except AttributeError as exc:
        raise InvalidModelTypeError(f"Error: {str(exc)}. Please ensure the type you're trying to parse into is correct")


@overload
def parse(event: dict[str, Any], model: type[T]) -> T: ...  # pragma: no cover


@overload
def parse(event: dict[str, Any], model: type[T], envelope: type[Envelope]) -> T: ...  # pragma: no cover


def parse(event: dict[str, Any], model: type[T], envelope: type[Envelope] | None = None):
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
    event:    dict
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
            ) from exc

    try:
        adapter = _retrieve_or_set_model_from_cache(model=model)

        logger.debug("Parsing and validating event model; no envelope used")
        return _parse_and_validate_event(data=event, adapter=adapter)

    # Pydantic raises PydanticSchemaGenerationError when the model is not a Pydantic model
    # This is seen in the tests where we pass a non-Pydantic model type to the parser or
    # when we pass a data structure that does not match the model (trying to parse a true/false/etc into a model)
    except PydanticSchemaGenerationError as exc:
        raise InvalidModelTypeError(f"The event supplied is unable to be validated into {type(model)}") from exc
    except AttributeError as exc:
        raise InvalidModelTypeError(
            f"Error: {str(exc)}. Please ensure the Input model inherits from BaseModel,\n"
            "and your payload adheres to the specified Input model structure.\n"
            f"Model={model}",
        ) from exc
