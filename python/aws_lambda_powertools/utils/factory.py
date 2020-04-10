import functools


def lambda_handler_decorator(decorator):
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
        def obfuscate_sensitive_data(handler, event, context, obfuscate_email=None):
            # Obfuscate email before calling Lambda handler
            if obfuscate_email:
                email = event.get('email', "")
                event['email'] = obfuscate_pii(email)
            
            response = handler(event, context)
            print(f"Lambda handler response: {response}")

        @obfuscate_sensitive_data(obfuscate_email=True)
        def lambda_handler(event, context):
            return True
    """

    @functools.wraps(decorator)
    def final_decorator(func=None, **kwargs):
        def decorated(func):
            """This is the decorator function that will be called when setting a decorator."""

            @functools.wraps(func)
            def wrapper(event, context):
                """Return decorator with decorated function incl. event/context/params"""
                return decorator(func, event, context, **kwargs)

            return wrapper

        # Return decorator if no params
        # Otherwise return decorator with params received
        if func is None:
            return decorated
        else:
            return decorated(func)

    return final_decorator
