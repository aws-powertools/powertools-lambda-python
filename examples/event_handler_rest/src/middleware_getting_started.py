from typing import Any, Callable

import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.api_gateway import BaseRouter

app = APIGatewayRestResolver()
logger = Logger()


def log_incoming_request(app: BaseRouter, get_response: Callable[..., Any], **context_args) -> Response:
    # Do Before processing here
    logger.info("Received request...", path=app.current_event.path)  # (1)!

    # Get Next response
    result = get_response(app, **context_args)  # (2)

    # Do After processing here

    # return the response
    return result  # (3)


@app.get("/todos", middlewares=[log_incoming_request])
def get_todos():
    todos: Response = requests.get("https://jsonplaceholder.typicode.com/todos")
    todos.raise_for_status()

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos.json()[:10]}
