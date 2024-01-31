import requests

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
    Response,
    content_types,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.get("/todos", compress=True)
@tracer.capture_method
def get_todos():
    todos: requests.Response = requests.get("https://jsonplaceholder.typicode.com/todos")
    todos.raise_for_status()

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos.json()[:10]}


@app.get("/todos/<todo_id>", compress=True)
@tracer.capture_method
def get_todo_by_id(todo_id: str):  # same example using Response class
    todos: requests.Response = requests.get(f"https://jsonplaceholder.typicode.com/todos/{todo_id}")
    todos.raise_for_status()

    return Response(status_code=200, content_type=content_types.APPLICATION_JSON, body=todos.json())


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
