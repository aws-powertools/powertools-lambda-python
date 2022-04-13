from aws_lambda_powertools.middleware_factory import lambda_handler_decorator


@lambda_handler_decorator
def middleware_before_after(handler, event, context):
    # logic_before_handler_execution()
    response = handler(event, context)
    # logic_after_handler_execution()
    return response


@middleware_before_after
def lambda_handler(event, context):
    ...
