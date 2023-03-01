import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import List

import requests
from requests import Response

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.data_classes.appsync import scalar_types_utils
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = AppSyncResolver()


class Todo(TypedDict, total=False):
    id: str  # noqa AA03 VNE003, required due to GraphQL Schema
    userId: str
    title: str
    completed: bool


@app.resolver(type_name="Query", field_name="getTodo")
@tracer.capture_method
def get_todo(
    id: str = "",  # noqa AA03 VNE003 shadows built-in id to match query argument, e.g., getTodo(id: "some_id")
) -> Todo:
    logger.info(f"Fetching Todo {id}")
    todos: Response = requests.get(f"https://jsonplaceholder.typicode.com/todos/{id}")
    todos.raise_for_status()

    return todos.json()


@app.resolver(type_name="Query", field_name="listTodos")
@tracer.capture_method
def list_todos() -> List[Todo]:
    todos: Response = requests.get("https://jsonplaceholder.typicode.com/todos")
    todos.raise_for_status()

    # for brevity, we'll limit to the first 10 only
    return todos.json()[:10]


@app.resolver(type_name="Mutation", field_name="createTodo")
@tracer.capture_method
def create_todo(title: str) -> Todo:
    payload = {"userId": scalar_types_utils.make_id(), "title": title, "completed": False}  # dummy UUID str
    todo: Response = requests.post("https://jsonplaceholder.typicode.com/todos", json=payload)
    todo.raise_for_status()

    return todo.json()


@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
