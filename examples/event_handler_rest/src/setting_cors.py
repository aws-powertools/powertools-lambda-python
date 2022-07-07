import requests
from requests import Response

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
cors_config = CORSConfig(allow_origin="https://example.com", max_age=300)
app = APIGatewayRestResolver(cors=cors_config)


@app.get("/todos")
@tracer.capture_method
def get_todos():
    todos: Response = requests.get("https://jsonplaceholder.typicode.com/todos")
    todos.raise_for_status()

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos.json()[:10]}


@app.get("/todos/<todo_id>")
@tracer.capture_method
def get_todo_by_id(todo_id: str):  # value come as str
    todos: Response = requests.get(f"https://jsonplaceholder.typicode.com/todos/{todo_id}")
    todos.raise_for_status()

    return {"todos": todos.json()}


@app.get("/healthcheck", cors=False)  # optionally removes CORS for a given route
@tracer.capture_method
def am_i_alive():
    return {"am_i_alive": "yes"}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
