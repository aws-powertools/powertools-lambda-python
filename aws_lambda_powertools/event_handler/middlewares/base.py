from abc import ABC, abstractmethod
from typing import Callable

from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, Response


class BaseMiddlewareHandler(ABC):
    """
    Base class for Middleware Handlers

    This is the middleware handler function where middleware logic is implemented.
    Here you have the option to execute code before and after the next handler in the
    middleware chain is called.  The next middleware handler is represented by `get_response`.


    ```python

    # Place code here for actions BEFORE the next middleware handler is called
    # or optionally raise an excpetion to short-circuit the middleware execution chain

    # Get the response from the NEXT middleware handler (optionally injecting custom
    # arguments into the get_response call)
    result: Response = get_response(app, my_custom_arg="handled", **kwargs)

    # Place code ehre for actions AFTER the next middleware handler is called

    return result
    ```

    To implement ERROR style middleware wrap the call to `get_response` in a `try..except`
    block - you can also catch specific types of errors this way so your middleware only handles
    specific types of exceptions.

    for example:
    ============

    ```python

    try:
        result: Response = get_response(app, my_custom_arg="handled", **kwargs)
    except MyCustomValidationException as e:
        # Make sure we send back a 400 resposne for any Custom Validation Exceptions.
        result.status_code = 400
        result.body = {"message": str(e)}

    return result
    ```

    :param app: The ApiGatewayResolver object
    :param get_response: The next middleware handler in the chain
    :param kwargs: Any additional arguments to pass to the next middleware handler
    :return: The response from the next middleware handler in the chain

    """

    @abstractmethod
    def __call__(self, app: ApiGatewayResolver, get_response: Callable, **kwargs) -> Response:
        """
        The Middleware handler function.

        :param app: The ApiGatewayResolver object
        :param get_response: The next middleware handler in the chain
        :param kwargs: Any additional arguments to pass to the next middleware handler
        :return: The response from the next middleware handler in the chain
        """
        raise NotImplementedError()
