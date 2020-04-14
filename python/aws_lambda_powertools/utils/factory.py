import functools
import logging
import os
from contextlib import contextmanager
from typing import Callable

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def lambda_handler_decorator(decorator: Callable):
    """Decorator factory for decorating Lambda handlers.

    You can use lambda_handler_decorator to create your own middlewares,
    where your function signature follows: fn(handler, event, context)

    You can also set your own key=value params: fn(handler, event, context, option=value)

    Example
    -------
    **Create a middleware no params**

        from aws_lambda_powertools.utils import lambda_handler_decorator

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

        from aws_lambda_powertools.utils import lambda_handler_decorator

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
    """

    @functools.wraps(decorator)
    def final_decorator(func: Callable = None, **kwargs):
        # If called with args return new func with args
        if func is None:
            return functools.partial(final_decorator, **kwargs)

        @functools.wraps(func)
        def wrapper(event, context):
            try:
                if os.getenv("POWERTOOLS_TRACE_MIDDLEWARES", False):
                    with _trace_middleware(middleware=decorator):
                        response = decorator(func, event, context, **kwargs)
                else:
                    response = decorator(func, event, context, **kwargs)
                return response
            except Exception as err:
                logger.error(f"Caught exception in {decorator.__qualname__}")
                raise err

        return wrapper

    return final_decorator


@contextmanager
def _trace_middleware(middleware):
    try:
        from ..tracing import Tracer

        tracer = Tracer()
        tracer.create_subsegment(name=f"## middleware {middleware.__qualname__}")
        yield
    finally:
        tracer.end_subsegment()
