"""
Primary interface for idempotent Lambda functions utility
"""

from __future__ import annotations

import functools
import logging
import os
import warnings
from inspect import isclass
from typing import TYPE_CHECKING, Any, cast

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import strtobool
from aws_lambda_powertools.shared.types import AnyCallableT
from aws_lambda_powertools.utilities.idempotency.base import IdempotencyHandler
from aws_lambda_powertools.utilities.idempotency.config import IdempotencyConfig
from aws_lambda_powertools.utilities.idempotency.serialization.base import (
    BaseIdempotencyModelSerializer,
    BaseIdempotencySerializer,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.idempotency.persistence.base import (
        BasePersistenceLayer,
    )
    from aws_lambda_powertools.utilities.typing import LambdaContext

from aws_lambda_powertools.warnings import PowertoolsUserWarning

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def idempotent(
    handler: Callable[[Any, LambdaContext], Any],
    event: dict[str, Any],
    context: LambdaContext,
    persistence_store: BasePersistenceLayer,
    config: IdempotencyConfig | None = None,
    key_prefix: str | None = None,
    **kwargs,
) -> Any:
    """
    Decorator to handle idempotency

    Parameters
    ----------
    handler: Callable
        Lambda's handler
    event: dict
        Lambda's Event
    context: dict
        Lambda's Context
    persistence_store: BasePersistenceLayer
        Instance of BasePersistenceLayer to store data
    config: IdempotencyConfig
        Configuration
    key_prefix: str | Optional
        Custom prefix for idempotency key: key_prefix#hash

    Example
    --------
    **Processes Lambda's event in an idempotent manner**

        from aws_lambda_powertools.utilities.idempotency import (
           idempotent, DynamoDBPersistenceLayer, IdempotencyConfig
        )

        idem_config=IdempotencyConfig(event_key_jmespath="body")
        persistence_layer = DynamoDBPersistenceLayer(table_name="idempotency_store")

        @idempotent(config=idem_config, persistence_store=persistence_layer)
        def handler(event, context):
            return {"StatusCode": 200}
    """

    # Skip idempotency controls when POWERTOOLS_IDEMPOTENCY_DISABLED has a truthy value
    # Raises a warning if not running in development mode
    if strtobool(os.getenv(constants.IDEMPOTENCY_DISABLED_ENV, "false")):
        warnings.warn(
            message="Disabling idempotency is intended for development environments only "
            "and should not be used in production.",
            category=PowertoolsUserWarning,
            stacklevel=2,
        )
        return handler(event, context, **kwargs)

    config = config or IdempotencyConfig()
    config.register_lambda_context(context)

    args = event, context
    idempotency_handler = IdempotencyHandler(
        function=handler,
        function_payload=event,
        config=config,
        persistence_store=persistence_store,
        key_prefix=key_prefix,
        function_args=args,
        function_kwargs=kwargs,
    )

    return idempotency_handler.handle()


def idempotent_function(
    function: AnyCallableT | None = None,
    *,
    data_keyword_argument: str,
    persistence_store: BasePersistenceLayer,
    config: IdempotencyConfig | None = None,
    output_serializer: BaseIdempotencySerializer | type[BaseIdempotencyModelSerializer] | None = None,
    key_prefix: str | None = None,
    **kwargs: Any,
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
    output_serializer: BaseIdempotencySerializer | type[BaseIdempotencyModelSerializer] | None
            Serializer to transform the data to and from a dictionary.
            If not supplied, no serialization is done via the NoOpSerializer.
            In case a serializer of type inheriting BaseIdempotencyModelSerializer is given,
            the serializer is derived from the function return type.
    key_prefix: str | Optional
        Custom prefix for idempotency key: key_prefix#hash

    Example
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

    if not function:
        return cast(
            AnyCallableT,
            functools.partial(
                idempotent_function,
                data_keyword_argument=data_keyword_argument,
                persistence_store=persistence_store,
                config=config,
                output_serializer=output_serializer,
                key_prefix=key_prefix,
                **kwargs,
            ),
        )

    if isclass(output_serializer) and issubclass(output_serializer, BaseIdempotencyModelSerializer):
        # instantiate an instance of the serializer class
        output_serializer = output_serializer.instantiate(function.__annotations__.get("return", None))

    config = config or IdempotencyConfig()

    @functools.wraps(function)
    def decorate(*args, **kwargs):
        # Skip idempotency controls when POWERTOOLS_IDEMPOTENCY_DISABLED has a truthy value
        # Raises a warning if not running in development mode
        if strtobool(os.getenv(constants.IDEMPOTENCY_DISABLED_ENV, "false")):
            warnings.warn(
                message="Disabling idempotency is intended for development environments only "
                "and should not be used in production.",
                category=PowertoolsUserWarning,
                stacklevel=2,
            )
            return function(*args, **kwargs)

        if data_keyword_argument not in kwargs:
            raise RuntimeError(
                f"Unable to extract '{data_keyword_argument}' from keyword arguments."
                f" Ensure this exists in your function's signature as well as the caller used it as a keyword argument",
            )

        payload = kwargs.get(data_keyword_argument)

        idempotency_handler = IdempotencyHandler(
            function=function,
            function_payload=payload,
            config=config,
            persistence_store=persistence_store,
            output_serializer=output_serializer,
            key_prefix=key_prefix,
            function_args=args,
            function_kwargs=kwargs,
        )

        return idempotency_handler.handle()

    return cast(AnyCallableT, decorate)
