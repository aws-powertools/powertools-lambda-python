import functools
import inspect
import logging
import os
from typing import Callable, Optional

from ..shared import constants
from ..shared.functions import resolve_truthy_env_var_choice
from ..tracing import Tracer
from .exceptions import MiddlewareInvalidArgumentError

logger = logging.getLogger(__name__)


def lambda_handler_decorator(decorator: Optional[Callable] = None, trace_execution: Optional[bool] = None):
    """Decorator factory for decorating Lambda handlers.

    You can use lambda_handler_decorator to create your own middlewares,
    where your function signature follows: `fn(handler, event, context)`

    Custom keyword arguments are also supported e.g. `fn(handler, event, context, option=value)`

    Middlewares created by this factory supports tracing to help you quickly troubleshoot
    any overhead that custom middlewares may cause - They will appear as custom subsegments.

    **Non-key value params are not supported** e.g. `fn(handler, event, context, option)`

    Environment variables
    ---------------------
    POWERTOOLS_TRACE_MIDDLEWARES : str
        uses `aws_lambda_powertools.tracing.Tracer`
        to create sub-segments per middleware (e.g. `"true", "True", "TRUE"`)

    Parameters
    ----------
    decorator: Callable
        Middleware to be wrapped by this factory
    trace_execution: bool
        Flag to explicitly enable trace execution for middlewares.\n
        `Env POWERTOOLS_TRACE_MIDDLEWARES="true"`

    Example
    -------
    **Create a middleware no params**

        from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

        @lambda_handler_decorator
        def log_response(handler, event, context):
            any_code_to_execute_before_lambda_handler()
            response = handler(event, context)
            any_code_to_execute_after_lambda_handler()
            print(f"Lambda handler response: {response}")

        @log_response
        def lambda_handler(event, context):
            return True

    **Create a middleware with params**

        from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

        @lambda_handler_decorator
        def obfuscate_sensitive_data(handler, event, context, fields=None):
            # Obfuscate email before calling Lambda handler
            if fields:
                for field in fields:
                    field = event.get(field, "")
                    event[field] = obfuscate_pii(field)

            response = handler(event, context)
            print(f"Lambda handler response: {response}")

        @obfuscate_sensitive_data(fields=["email"])
        def lambda_handler(event, context):
            return True

    **Trace execution of custom middleware**

        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

        tracer = Tracer(service="payment") # or via env var
        ...
        @lambda_handler_decorator(trace_execution=True)
        def log_response(handler, event, context):
            ...

        @tracer.capture_lambda_handler
        @log_response
        def lambda_handler(event, context):
            return True

    Limitations
    -----------
    * Async middlewares not supported
    * Classes, class methods middlewares not supported

    Raises
    ------
    MiddlewareInvalidArgumentError
        When middleware receives non keyword=arguments
    """

    if decorator is None:
        return functools.partial(lambda_handler_decorator, trace_execution=trace_execution)

    trace_execution = resolve_truthy_env_var_choice(
        env=os.getenv(constants.MIDDLEWARE_FACTORY_TRACE_ENV, "false"), choice=trace_execution
    )

    @functools.wraps(decorator)
    def final_decorator(func: Optional[Callable] = None, **kwargs):
        # If called with kwargs return new func with kwargs
        if func is None:
            return functools.partial(final_decorator, **kwargs)

        if not inspect.isfunction(func):
            # @custom_middleware(True) vs @custom_middleware(log_event=True)
            raise MiddlewareInvalidArgumentError(
                f"Only keyword arguments is supported for middlewares: {decorator.__qualname__} received {func}"
            )

        @functools.wraps(func)
        def wrapper(event, context):
            try:
                middleware = functools.partial(decorator, func, event, context, **kwargs)
                if trace_execution:
                    tracer = Tracer(auto_patch=False)
                    with tracer.provider.in_subsegment(name=f"## {decorator.__qualname__}"):
                        response = middleware()
                else:
                    response = middleware()
                return response
            except Exception:
                logger.exception(f"Caught exception in {decorator.__qualname__}")
                raise

        return wrapper

    return final_decorator
