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
    api_key: str = router.current_event.get_header_value(name="X-Api-Key", case_sensitive=True, default_value="")

    todos: Response = requests.get(endpoint, headers={"X-Api-Key": api_key})
    todos.raise_for_status()

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos.json()[:10]}


@router.get("/todos/<todo_id>")
@tracer.capture_method
def get_todo_by_id(todo_id: str):  # value come as str
    api_key: str = router.current_event.get_header_value(name="X-Api-Key", case_sensitive=True, default_value="")  # type: ignore[assignment] # sentinel typing # noqa: E501

    todos: Response = requests.get(f"{endpoint}/{todo_id}", headers={"X-Api-Key": api_key})
    todos.raise_for_status()

    return {"todos": todos.json()}
