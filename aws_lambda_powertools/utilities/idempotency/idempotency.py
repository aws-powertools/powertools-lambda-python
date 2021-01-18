"""
Primary interface for idempotent Lambda functions utility
"""
import logging
from typing import Any, Callable, Dict

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

from ..typing import LambdaContext
from .exceptions import AlreadyInProgressError, ItemNotFoundError
from .persistence import STATUS_CONSTANTS, BasePersistenceLayer

logger = logging.getLogger(__name__)


def default_error_callback():
    raise


@lambda_handler_decorator
def idempotent(
    handler: Callable[[Any, LambdaContext], Any],
    event: Dict[str, Any],
    context: LambdaContext,
    persistence: BasePersistenceLayer,
) -> Any:
    """
    Middleware to handle idempotency

    Parameters
    ----------
    handler: Callable
        Lambda's handler
    event: Dict
        Lambda's Event
    context: Dict
        Lambda's Context
    persistence: BasePersistenceLayer
        Instance of BasePersistenceLayer to store data

    Examples
    --------
    **Processes Lambda's event in an idempotent manner**
        >>> from aws_lambda_powertools.utilities.idempotency import idempotent, DynamoDBPersistenceLayer
        >>>
        >>> persistence_store = DynamoDBPersistenceLayer(event_key="body", table_name="idempotency_store")
        >>>
        >>> @idempotent(persistence=persistence_store)
        >>> def handler(event, context):
        >>>     return {"StatusCode": 200}
    """

    persistence_instance = persistence
    try:
        event_record = persistence_instance.get_record(event)
    except ItemNotFoundError:
        persistence_instance.save_inprogress(event=event)
        return _call_lambda(handler=handler, persistence_instance=persistence_instance, event=event, context=context)

    if event_record.status == STATUS_CONSTANTS["EXPIRED"]:
        return _call_lambda(handler=handler, persistence_instance=persistence_instance, event=event, context=context)

    if event_record.status == STATUS_CONSTANTS["INPROGRESS"]:
        raise AlreadyInProgressError(
            f"Execution already in progress with idempotency key: "
            f"{persistence_instance.event_key}={event_record.idempotency_key}"
        )

    if event_record.status == STATUS_CONSTANTS["COMPLETED"]:
        return event_record.response_json_as_dict()


def _call_lambda(
    handler: Callable, persistence_instance: BasePersistenceLayer, event: Dict[str, Any], context: LambdaContext
) -> Any:
    """

    Parameters
    ----------
    handler: Callable
        Lambda handler
    persistence_instance: BasePersistenceLayer
        Instance of persistence layer
    event
        Lambda event
    context
        Lambda context
    """
    try:
        handler_response = handler(event, context)
    except Exception as ex:
        persistence_instance.save_error(event=event, exception=ex)
        raise
    else:
        persistence_instance.save_success(event=event, result=handler_response)
    return handler_response
