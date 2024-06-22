import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler, NextMiddleware

app = APIGatewayRestResolver()
logger = Logger()


class CorrelationIdMiddleware(BaseMiddlewareHandler):
    def __init__(self, header: str):  # (1)!
        """Extract and inject correlation ID in response

        Parameters
        ----------
        header : str
            HTTP Header to extract correlation ID
        """
        super().__init__()
        self.header = header

    def handler(self, app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:  # (2)!
        request_id = app.current_event.request_context.request_id
        correlation_id = app.current_event.headers.get(self.header, request_id)

        response = next_middleware(app)  # (3)!
        response.headers[self.header] = correlation_id

        return response


@app.get("/todos", middlewares=[CorrelationIdMiddleware(header="x-correlation-id")])  # (4)!
def get_todos():
    todos: requests.Response = requests.get("https://jsonplaceholder.typicode.com/todos")
    todos.raise_for_status()

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos.json()[:10]}


@logger.inject_lambda_context
def lambda_handler(event, context):
    return app.resolve(event, context)
