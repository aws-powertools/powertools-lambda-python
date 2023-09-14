from abc import ABC, abstractmethod
from typing import Generic

from aws_lambda_powertools.event_handler.api_gateway import Response
from aws_lambda_powertools.event_handler.types import EventHandlerInstance
from aws_lambda_powertools.shared.types import Protocol


class NextMiddleware(Protocol):
    def __call__(self, app: EventHandlerInstance) -> Response:
        """Protocol for callback regardless of next_middleware(app), get_response(app) etc"""
        ...

    def __name__(self) -> str:  # noqa A003
        """Protocol for name of the Middleware"""
        ...


class BaseMiddlewareHandler(Generic[EventHandlerInstance], ABC):
    """Base implementation for Middlewares to run code before and after in a chain.


    This is the middleware handler function where middleware logic is implemented.
    The next middleware handler is represented by `next_middleware`, returning a Response object.

    Examples
    --------

    **Correlation ID Middleware**

    ```python
    import requests

    from aws_lambda_powertools import Logger
    from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
    from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler, NextMiddleware

    app = APIGatewayRestResolver()
    logger = Logger()


    class CorrelationIdMiddleware(BaseMiddlewareHandler):
        def __init__(self, header: str):
            super().__init__()
            self.header = header

        def handler(self, app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
            # BEFORE logic
            request_id = app.current_event.request_context.request_id
            correlation_id = app.current_event.get_header_value(
                name=self.header,
                default_value=request_id,
            )

            # Call next middleware or route handler ('/todos')
            response = next_middleware(app)

            # AFTER logic
            response.headers[self.header] = correlation_id

            return response


    @app.get("/todos", middlewares=[CorrelationIdMiddleware(header="x-correlation-id")])
    def get_todos():
        todos: requests.Response = requests.get("https://jsonplaceholder.typicode.com/todos")
        todos.raise_for_status()

        # for brevity, we'll limit to the first 10 only
        return {"todos": todos.json()[:10]}


    @logger.inject_lambda_context
    def lambda_handler(event, context):
        return app.resolve(event, context)

    ```

    """

    @abstractmethod
    def handler(self, app: EventHandlerInstance, next_middleware: NextMiddleware) -> Response:
        """
        The Middleware Handler

        Parameters
        ----------
        app: EventHandlerInstance
            An instance of an Event Handler that implements ApiGatewayResolver
        next_middleware: NextMiddleware
            The next middleware handler in the chain

        Returns
        -------
        Response
            The response from the next middleware handler in the chain

        """
        raise NotImplementedError()

    @property
    def __name__(self) -> str:  # noqa A003
        return str(self.__class__.__name__)

    def __call__(self, app: EventHandlerInstance, next_middleware: NextMiddleware) -> Response:
        """
        The Middleware handler function.

        Parameters
        ----------
        app: ApiGatewayResolver
            An instance of an Event Handler that implements ApiGatewayResolver
        next_middleware: NextMiddleware
            The next middleware handler in the chain

        Returns
        -------
        Response
            The response from the next middleware handler in the chain
        """
        return self.handler(app, next_middleware)
