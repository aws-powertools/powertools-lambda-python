"""
Primary interface for idempotent Lambda functions utility
"""
import functools
import logging
import os
from typing import Any, Callable, Dict, Optional, cast

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.shared.constants import IDEMPOTENCY_DISABLED_ENV
from aws_lambda_powertools.shared.types import AnyCallableT
from aws_lambda_powertools.utilities.idempotency.base import IdempotencyHandler
from aws_lambda_powertools.utilities.idempotency.config import IdempotencyConfig
from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def idempotent(
    handler: Callable[[Any, LambdaContext], Any],
    event: Dict[str, Any],
    context: LambdaContext,
    persistence_store: BasePersistenceLayer,
    config: Optional[IdempotencyConfig] = None,
    **kwargs,
) -> Any:
    """
    Decorator to handle idempotency

    Parameters
    ----------
    handler: Callable
        Lambda's handler
    event: Dict
        Lambda's Event
    context: Dict
        Lambda's Context
    persistence_store: BasePersistenceLayer
        Instance of BasePersistenceLayer to store data
    config: IdempotencyConfig
        Configuration

    Examples
    --------
    **Processes Lambda's event in an idempotent manner**

        >>> from aws_lambda_powertools.utilities.idempotency import (
        >>>    idempotent, DynamoDBPersistenceLayer, IdempotencyConfig
        >>> )
        >>>
        >>> idem_config=IdempotencyConfig(event_key_jmespath="body")
        >>> persistence_layer = DynamoDBPersistenceLayer(table_name="idempotency_store")
        >>>
        >>> @idempotent(config=idem_config, persistence_store=persistence_layer)
        >>> def handler(event, context):
        >>>     return {"StatusCode": 200}
    """

    if os.getenv(IDEMPOTENCY_DISABLED_ENV):
        return handler(event, context)

    config = config or IdempotencyConfig()
    args = event, context
    idempotency_handler = IdempotencyHandler(
        function=handler,
        function_payload=event,
        config=config,
        persistence_store=persistence_store,
        function_args=args,
        function_kwargs=kwargs,
    )

    return idempotency_handler.handle()


def idempotent_function(
    function: Optional[AnyCallableT] = None,
    *,
    data_keyword_argument: str,
    persistence_store: BasePersistenceLayer,
    config: Optional[IdempotencyConfig] = None,
) -> Any:
    """
    Decorator to handle idempotency of any function

    Parameters
    ----------
    function: Callable
        Function to be decorated
    data_keyword_argument: str
        Keyword parameter name in function's signature that we should hash as idempotency key, e.g. "order"
    persistence_store: BasePersistenceLayer
        Instance of BasePersistenceLayer to store data
    config: IdempotencyConfig
        Configuration

    Examples
    --------
    **Processes an order in an idempotent manner**

        from aws_lambda_powertools.utilities.idempotency import (
           idempotent_function, DynamoDBPersistenceLayer, IdempotencyConfig
        )

        idem_config=IdempotencyConfig(event_key_jmespath="order_id")
        persistence_layer = DynamoDBPersistenceLayer(table_name="idempotency_store")

        @idempotent_function(data_keyword_argument="order", config=idem_config, persistence_store=persistence_layer)
        def process_order(customer_id: str, order: dict, **kwargs):
            return {"StatusCode": 200}
    """

    if function is None:
        return cast(
            AnyCallableT,
            functools.partial(
                idempotent_function,
                data_keyword_argument=data_keyword_argument,
                persistence_store=persistence_store,
                config=config,
            ),
        )

    config = config or IdempotencyConfig()

    @functools.wraps(function)
    def decorate(*args, **kwargs):
        if os.getenv(IDEMPOTENCY_DISABLED_ENV):
            return function(*args, **kwargs)

        payload = kwargs.get(data_keyword_argument)

        if payload is None:
            raise RuntimeError(
                f"Unable to extract '{data_keyword_argument}' from keyword arguments."
                f" Ensure this exists in your function's signature as well as the caller used it as a keyword argument"
            )

        idempotency_handler = IdempotencyHandler(
            function=function,
            function_payload=payload,
            config=config,
            persistence_store=persistence_store,
            function_args=args,
            function_kwargs=kwargs,
        )

        return idempotency_handler.handle()

    return cast(AnyCallableT, decorate)
