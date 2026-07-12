from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.data_classes.common import DictWrapper
    from aws_lambda_powertools.utilities.typing import LambdaContext

DataClassT = TypeVar("DataClassT", bound="DictWrapper")
OutputT = TypeVar("OutputT")


class _EventSourceDecorator(Protocol):
    """Annotation of event_source, that lambda_handler_decorator erases at runtime."""

    def __call__(
        self,
        *,
        data_class: type[DataClassT],
    ) -> Callable[
        [Callable[[DataClassT, LambdaContext], OutputT]],
        Callable[[dict[str, Any], LambdaContext], OutputT],
    ]: ...


@lambda_handler_decorator
def _event_source(
    handler: Callable[[Any, LambdaContext], OutputT],
    event: dict[str, Any],
    context: LambdaContext,
    data_class: type[DataClassT],
) -> OutputT:
    """Middleware to create an instance of the passed in event source data class

    Parameters
    ----------
    handler: Callable
        Lambda's handler
    event: dict[str, Any]
        Lambda's Event
    context: LambdaContext
        Lambda's Context
    data_class: type[DictWrapper]
        Data class type to instantiate

    Example
    --------

    **Sample usage**

        from aws_lambda_powertools.utilities.data_classes import S3Event, event_source

        @event_source(data_class=S3Event)
        def handler(event: S3Event, context):
             return {"key": event.object_key}
    """
    return handler(data_class(event), context)


event_source = cast(_EventSourceDecorator, _event_source)
