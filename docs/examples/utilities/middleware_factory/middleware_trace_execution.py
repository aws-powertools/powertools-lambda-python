from aws_lambda_powertools.middleware_factory import lambda_handler_decorator


@lambda_handler_decorator(trace_execution=True)
def my_middleware(handler, event, context):
    return handler(event, context)


@my_middleware
def lambda_handler(event, context):
    ...
