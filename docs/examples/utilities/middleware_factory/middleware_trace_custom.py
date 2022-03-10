from aws_lambda_powertools import Tracer
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator


@lambda_handler_decorator(trace_execution=True)
def middleware_name(handler, event, context):
    # tracer = Tracer() # Takes a copy of an existing tracer instance
    # tracer.add_annotation...
    # tracer.add_metadata...
    return handler(event, context)
