import asyncio

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator


@lambda_handler_decorator
def async_lambda_handler(handler, event, context):
    return asyncio.run(handler(event, context))
