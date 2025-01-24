from urllib.parse import quote

import requests
from requests import Response

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.event_handler.api_gateway import Router

tracer = Tracer()
router = Router()

endpoint = "https://jsonplaceholder.typicode.com/todos"


@router.get("/todos")
@tracer.capture_method
def get_todos():
    api_key = router.current_event.headers["X-Api-Key"]

    todos: Response = requests.get(endpoint, headers={"X-Api-Key": api_key})
    todos.raise_for_status()

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos.json()[:10]}


@router.get("/todos/<todo_id>")
@tracer.capture_method
def get_todo_by_id(todo_id: str):  # value come as str
    api_key = router.current_event.headers["X-Api-Key"]

    todo_id = quote(todo_id, safe="")
    todos: Response = requests.get(f"{endpoint}/{todo_id}", headers={"X-Api-Key": api_key})
    todos.raise_for_status()

    return {"todos": todos.json()}
