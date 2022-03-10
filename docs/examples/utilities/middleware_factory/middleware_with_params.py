from typing import List

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator


@lambda_handler_decorator
def obfuscate_sensitive_data(handler, event, context, fields: List = None):
    # Obfuscate email before calling Lambda handler
    if fields:
        for field in fields:
            if field in event:
                event[field] = obfuscate(event[field])

    return handler(event, context)


@obfuscate_sensitive_data(fields=["email"])
def lambda_handler(event, context):
    ...
