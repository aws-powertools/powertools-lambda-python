import logging
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ValidationError

from ...middleware_factory import lambda_handler_decorator
from ..typing import LambdaContext
from .envelopes.base import BaseEnvelope
from .exceptions import InvalidEnvelopeError, InvalidModelTypeError, ModelValidationError

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def event_parser(
    handler: Callable[[Dict, Any], Any],
    event: Dict[str, Any],
    context: LambdaContext,
    model: BaseModel,
    envelope: Optional[BaseEnvelope] = None,
) -> Any:
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
    model:   BaseModel
        Your data model that will replace the event.
    envelope: BaseEnvelope
        Optional envelope to extract the model from

    Raises
    ------
    ModelValidationError
        When input event does not conform with model provided
    InvalidModelTypeError
        When model given does not implement BaseModel
    InvalidEnvelopeError
        When envelope given does not implement BaseEnvelope
    """
    parsed_event = parse(event=event, model=model, envelope=envelope)
    logger.debug(f"Calling handler {handler.__name__}")
    return handler(parsed_event, context)


def parse(event: Dict[str, Any], model: BaseModel, envelope: Optional[BaseEnvelope] = None) -> Any:
    """Standalone function to parse & validate events using Pydantic models

    Typically used when you need fine-grained control over error handling compared to event_parser decorator.

    Example
    -------

    **Lambda handler decorator to parse & validate event**

        from aws_lambda_powertools.utilities.parser.exceptions import ModelValidationError

        class Order(BaseModel):
            id: int
            description: str
            ...

        def handler(event: Order, context: LambdaContext):
            try:
                parse(model=Order)
            except ModelValidationError:
                ...

    **Lambda handler decorator to parse & validate event - using built-in envelope**

        class Order(BaseModel):
            id: int
            description: str
            ...

        def handler(event: Order, context: LambdaContext):
            try:
                parse(model=Order, envelope=envelopes.EVENTBRIDGE)
            except ModelValidationError:
                ...

    Parameters
    ----------
    event:    Dict
        Lambda event to be parsed & validated
    model:   BaseModel
        Your data model that will replace the event
    envelope: BaseEnvelope
        Optional envelope to extract the model from

    Raises
    ------
    ModelValidationError
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
        except (ValidationError, TypeError) as e:
            raise ModelValidationError(f"Input event does not conform with model, envelope={envelope}") from e

    try:
        logger.debug("Parsing and validating event model; no envelope used")
        if isinstance(event, str):
            return model.parse_raw(event)

        return model.parse_obj(event)
    except (ValidationError, TypeError) as e:
        raise ModelValidationError("Input event does not conform with model") from e
    except AttributeError:
        raise InvalidModelTypeError("Input model must implement BaseModel")
