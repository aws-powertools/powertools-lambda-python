from abc import ABC, abstractmethod
from typing import Any, Callable

from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, Response


class BaseMiddlewareHandler(ABC):
    """
    Base class for Middleware Handlers

    This is the middleware handler function where middleware logic is implemented.
    Here you have the option to execute code before and after the next handler in the
    middleware chain is called.  The next middleware handler is represented by `get_response`.


    ```python

    # Place code here for actions BEFORE the next middleware handler is called
    # or optionally raise an exception to short-circuit the middleware execution chain

    # Get the response from the NEXT middleware handler (optionally injecting custom
    # arguments into the get_response call)
    result: Response = get_response(app, my_custom_arg="handled", **kwargs)

    # Place code here for actions AFTER the next middleware handler is called

    return result
    ```

    To implement ERROR style middleware wrap the call to `get_response` in a `try..except`
    block - you can also catch specific types of errors this way so your middleware only handles
    specific types of exceptions.

    for example:

    ```python

    try:
        result: Response = get_response(app, my_custom_arg="handled", **kwargs)
    except MyCustomValidationException as e:
        # Make sure we send back a 400 response for any Custom Validation Exceptions.
        result.status_code = 400
        result.body = {"message": "Failed validation"}
        logger.exception(f"Failed validation when handling route: {app.current_event.path}")

    return result
    ```

    To short-circuit the middleware execution chain you can either raise an exception to cause
    the function call stack to unwind naturally OR you can simple not call the `get_response`
    handler to get the response from the next middleware handler in the chain.

    for example:
    If you wanted to ensure API callers cannot call a DELETE verb on your API (regardless of defined routes)
    you could do so with the following middleware implementation.

    ```python
    # If invalid http_method is used - return a 405 error
    # and return early to short-circuit the middleware execution chain
    if app.current_event.http_method == "DELETE":
        return Response(status_code=405, body={"message": "DELETE verb not allowed"})


    # Call the next middleware in the chain (needed for when condition above is valid)
    return get_response(app, **kwargs)

    """

    @abstractmethod
    def handler(self, app: ApiGatewayResolver, get_response: Callable[..., Any], **kwargs) -> Response:
        """
        The Middleware Handler

        Parameters
        ----------
        app: ApiGatewayResolver
            The ApiGatewayResolver object
        get_response: Callable[..., Any]
            The next middleware handler in the chain
        kwargs: Any
            Any additional arguments to pass to the next middleware handler

        Returns
        -------
        Response
            The response from the next middleware handler in the chain

        """
        raise NotImplementedError()

    def __call__(self, app: ApiGatewayResolver, get_response: Callable[..., Any], **kwargs) -> Response:
        """
        The Middleware handler function.

        Parameters
        ----------
        app: ApiGatewayResolver
            The ApiGatewayResolver object
        get_response: Callable[...,Any]
            The next middleware handler in the chain
        kwargs:
            Any additional arguments to pass to the next middleware handler

        Returns
        -------
        Response
            The response from the next middleware handler in the chain
        """
        return self.handler(app, get_response, **kwargs)
