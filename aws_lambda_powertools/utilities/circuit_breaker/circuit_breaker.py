"""
Primary interface for the Circuit Breaker utility.
"""

from __future__ import annotations

import functools
import inspect
import logging
import os
import warnings
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import strtobool
from aws_lambda_powertools.utilities.circuit_breaker.base import CircuitBreakerHandler
from aws_lambda_powertools.utilities.circuit_breaker.config import CircuitBreakerConfig
from aws_lambda_powertools.warnings import PowertoolsUserWarning

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.circuit_breaker.persistence.base import (
        CircuitBreakerPersistenceLayer,
    )

logger = logging.getLogger(__name__)


def circuit_breaker(
    name: str,
    persistence_store: CircuitBreakerPersistenceLayer,
    on_circuit_open: Callable | None = None,
    on_transition: Callable | None = None,
    config: CircuitBreakerConfig | None = None,
) -> Callable:
    """
    Protect a function that calls an unhealthy-prone downstream with a circuit breaker.

    Wrap the function that makes the downstream call, not the whole Lambda handler, so a
    tripped circuit reflects one dependency rather than unrelated handler logic.

    When the circuit is open the protected function is not called. Instead, if an
    ``on_circuit_open`` callback is registered it runs and its return value becomes the
    call's result; otherwise :class:`CircuitBreakerOpenError` is raised.

    Parameters
    ----------
    name : str
        Unique circuit name. Each name is an independent circuit; a function calling
        several backends should use one circuit per backend.
    persistence_store : CircuitBreakerPersistenceLayer
        Shared state store (for example ``CircuitBreakerDynamoDBPersistence``).
    on_circuit_open : Callable | None
        Called when the circuit is open, with the protected function's own arguments
        (positional stay positional, keyword stay keyword) plus a trailing ``circuit``
        keyword argument carrying a ``CircuitInfo``. Its return value becomes the call's
        result. If ``None``, an open circuit raises ``CircuitBreakerOpenError``.
    on_transition : Callable | None
        Called with a single ``CircuitTransition`` argument whenever the circuit changes
        state (open, probe, close, reopen). Fires only on transitions, never on the
        per-invocation hot path, so it is a safe place to emit a CloudWatch metric. Any
        exception it raises is swallowed and logged so observability never breaks the
        protected call.
    config : CircuitBreakerConfig | None
        Tunables. Defaults to ``CircuitBreakerConfig()`` when omitted.

    Returns
    -------
    Callable
        The decorated function.

    Example
    -------
    **Protect a payment backend, buffering rejected requests**

        from aws_lambda_powertools.utilities.circuit_breaker import circuit_breaker, CircuitInfo
        from aws_lambda_powertools.utilities.circuit_breaker.persistence import (
            CircuitBreakerDynamoDBPersistence,
        )

        persistence = CircuitBreakerDynamoDBPersistence(table_name="CircuitBreakerState")

        def buffer(order: dict, circuit: CircuitInfo):
            sqs.send_message(QueueUrl=url, MessageBody=json.dumps(order))

        @circuit_breaker(name="payment-backend", persistence_store=persistence, on_circuit_open=buffer)
        def charge(order: dict) -> dict:
            return payment_api.charge(order)
    """
    config = config or CircuitBreakerConfig()

    def decorator(function: Callable) -> Callable:
        def disabled() -> bool:
            # Skip the circuit entirely when disabled (development only).
            if not strtobool(os.getenv(constants.CIRCUIT_BREAKER_DISABLED_ENV, "false")):
                return False
            warnings.warn(
                message="Disabling the circuit breaker is intended for development environments only "
                "and should not be used in production.",
                category=PowertoolsUserWarning,
                stacklevel=3,
            )
            return True

        def build_handler(args: tuple, kwargs: dict) -> CircuitBreakerHandler:
            return CircuitBreakerHandler(
                function=function,
                name=name,
                config=config,
                persistence_store=persistence_store,
                on_circuit_open=on_circuit_open,
                on_transition=on_transition,
                function_args=args,
                function_kwargs=kwargs,
            )

        if inspect.iscoroutinefunction(function):

            @functools.wraps(function)
            async def async_wrapper(*args, **kwargs) -> Any:
                if disabled():
                    return await function(*args, **kwargs)
                return await build_handler(args, kwargs).handle_async()

            return async_wrapper

        @functools.wraps(function)
        def wrapper(*args, **kwargs) -> Any:
            if disabled():
                return function(*args, **kwargs)
            return build_handler(args, kwargs).handle()

        return wrapper

    return decorator
